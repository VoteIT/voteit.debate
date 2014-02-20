import unittest

from pyramid import testing
from pyramid.traversal import find_interface
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.meeting import Meeting
from voteit.core.models.user import User
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.irl.models.interfaces import IParticipantNumbers

from voteit.debate.interfaces import ISpeakerList
from voteit.debate.interfaces import ISpeakerLists
from voteit.debate.interfaces import ISpeakerListPlugin


def _fixture(config):
    root = bootstrap_and_fixture(config)
    root['m'] = Meeting()
    _add_pn_users(config, root['m'])
    return root

def _add_pn_users(config, meeting):
    config.include('voteit.irl.models.participant_numbers')
    root = meeting.__parent__
    participant_numbers = config.registry.getAdapter(meeting, IParticipantNumbers)
    participant_numbers.new_tickets('admin', 1, 20)
    participant_numbers.token_to_number.clear()
    for i in range(1, 16):
        participant_numbers.token_to_number[str(i)] = i
    for m in range(1, 6):
        root.users['male%s' % m] = User(gender = 'male')
        participant_numbers.claim_ticket('male%s' % m, str(m))
    for f in range(11, 16):
        root.users['female%s' % f] = User(gender = 'female')
        participant_numbers.claim_ticket('female%s' % f, str(f))


class PNToGenderDictTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        request.context = AgendaItem()
        self.config = testing.setUp(request = request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _fut(self):
        from voteit.debate.plugins.female_priority import pn_to_gender_dict
        return pn_to_gender_dict

    def test_get(self):
        root = _fixture(self.config)
        res = self._fut(root['m'])
        self.assertEqual({1: 'male', 2: 'male', 3: 'male', 4: 'male', 5: 'male',
                          11: 'female', 12: 'female', 13: 'female', 14: 'female', 15: 'female'},
                         res)


class FemalePNsTests(unittest.TestCase):
     
    def setUp(self):
        request = testing.DummyRequest()
        request.context = AgendaItem()
        self.config = testing.setUp(request = request)
 
    def tearDown(self):
        testing.tearDown()
     
    @property
    def _fut(self):
        from voteit.debate.plugins.female_priority import female_pns
        return female_pns
 
    def test_get_all(self):
        root = _fixture(self.config)
        res = self._fut(root['m'], None, *range(20))
        self.assertEqual(frozenset([11, 12, 13, 14, 15]), res)


class FemalePrioritySLTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        request.context = AgendaItem()
        self.config = testing.setUp(request = request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from voteit.debate.plugins.female_priority import FemalePrioritySL
        return FemalePrioritySL

    def _fixture(self, **kw):
        self.config.registry.settings['plugins'] = u''
        self.config.include('voteit.debate')
        self.config.include('voteit.debate.plugins.female_priority')
        root = _fixture(self.config)
        meeting = root['m']
        meeting.set_field_value('speaker_list_plugin', self._cut.plugin_name)
        meeting.set_field_appstruct(kw)
        meeting['ai'] = ai = AgendaItem()
        ai.uid = 'uid'
        request = testing.DummyRequest()
        lists = request.registry.getAdapter(meeting, ISpeakerLists)
        lists.add_contextual_list(ai)
        return lists

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerListPlugin, self._cut))

    def test_verify_object(self):
        lists = self._fixture()
        obj = lists['uid/1']
        self.failUnless(verifyObject(ISpeakerListPlugin, obj))

    def test_correct_adapter_fetched(self):
        lists = self._fixture()
        obj = lists['uid/1']
        self.assertIsInstance(obj, self._cut)

    def test_male_dont_bypass(self):
        lists = self._fixture(safe_positions = 1)
        obj = lists['uid/1']
        obj.speakers.extend([1, 2, 11, 3, 4])
        obj.add(5)
        self.assertEqual(obj.speakers, [1, 2, 11, 3, 4, 5])

    def test_female_bypasses_male(self):
        lists = self._fixture(safe_positions = 0)
        obj = lists['uid/1']
        obj.speakers.extend([1, 2, 3, 4, 5])
        obj.add(11)
        self.assertEqual(obj.speakers, [11, 1, 2, 3, 4, 5])

    def test_female_bypasses_male_until_safe(self):
        lists = self._fixture(safe_positions = 1)
        obj = lists['uid/1']
        obj.speakers.extend([1, 2, 3, 4, 5])
        obj.add(11)
        self.assertEqual(obj.speakers, [1, 11, 2, 3, 4, 5])

    def test_female_bypasses_male_but_only_every_second(self):
        lists = self._fixture(safe_positions = 1)
        obj = lists['uid/1']
        obj.speakers.extend([1, 11, 2, 12, 3, 4, 5])
        obj.add(13)
        self.assertEqual(obj.speakers, [1, 11, 2, 12, 3, 13, 4, 5])
