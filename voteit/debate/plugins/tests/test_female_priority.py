import unittest

from pyramid import testing
from pyramid.request import apply_request_extensions
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from voteit.core.models.meeting import Meeting
from voteit.core.models.user import User
from voteit.core.testing_helpers import bootstrap_and_fixture
from voteit.irl.models.interfaces import IParticipantNumbers

from voteit.debate.interfaces import ISpeakerListSettings
from voteit.debate.interfaces import ISpeakerLists


class FemalePriorityListsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        self.config.include('voteit.debate.schemas')
        self.config.include('voteit.debate.models')
        self.request = testing.DummyRequest()
        apply_request_extensions(self.request)
        self.config.begin(self.request)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.debate.plugins.female_priority import FemalePriorityLists
        return FemalePriorityLists

    @property
    def _sl(self):
        from voteit.debate.models import SpeakerList
        return SpeakerList

    def _setup_meeting(self, meeting, speaker_list_count=1, safe_positions=0, **kw):
        settings = ISpeakerListSettings(meeting)
        settings.update(
            speaker_list_plugin='female_priority',
            speaker_list_count=speaker_list_count,
            safe_positions=safe_positions,
            **kw)
        return settings

    def _fixture(self):
        self.config.include('voteit.irl.models.participant_numbers')
        self.config.include('voteit.debate.plugins.female_priority')
        root = bootstrap_and_fixture(self.config)
        root['m'] = meeting = Meeting()
        self.request.root = root
        self.request.meeting = meeting
        participant_numbers = IParticipantNumbers(meeting)
        participant_numbers.new_tickets('admin', 1, 20)
        participant_numbers.token_to_number.clear()
        for i in range(1, 16):
            participant_numbers.token_to_number[str(i)] = i
        for m in range(1, 6):
            root.users['male%s' % m] = User(gender='male')
            participant_numbers.claim_ticket('male%s' % m, str(m))
        for f in range(11, 16):
            root.users['female%s' % f] = User(gender='female')
            participant_numbers.claim_ticket('female%s' % f, str(f))
        lists = self._cut(meeting, self.request)
        sl = self._sl('one')
        sl.__parent__ = meeting
        lists['one'] = sl
        self._setup_meeting(meeting)
        return lists

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerLists, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerLists, self._cut(Meeting(), self.request)))

    def test_male_dont_bypass(self):
        lists = self._fixture()
        sl = lists['one']
        sl.extend([1, 2, 11, 3, 4])
        lists.add_to_list(5, sl)
        # Note: update_order updates previous too.
        self.assertEqual(sl, [1, 11, 2, 3, 4, 5])

    def test_female_bypasses_male(self):
        lists = self._fixture()
        sl = lists['one']
        sl.extend([1, 2, 3, 4, 5])
        lists.add_to_list(11, sl)
        self.assertEqual(sl, [1, 11, 2, 3, 4, 5])

    def test_female_pns(self):
        lists = self._fixture()
        sl = lists['one']
        sl.extend(range(1, 16))
        self.assertEqual(lists.female_pns(sl), frozenset(range(11, 16)))

    def test_female_bypasses_male_until_safe(self):
        lists = self._fixture()
        self._setup_meeting(lists.context, safe_positions=1)
        sl = lists['one']
        sl.extend([1, 2, 3, 4, 5])
        lists.add_to_list(11, sl)
        self.assertEqual(sl, [1, 11, 2, 3, 4, 5])

    def test_female_bypasses_male_but_only_every_second(self):
        lists = self._fixture()
        sl = lists['one']
        sl.extend([1, 11, 2, 12, 3, 4, 5])
        lists.add_to_list(13, sl)
        self.assertEqual(sl, [1, 11, 2, 12, 3, 13, 4, 5])

    def test_female_last_not_bypassed(self):
        lists = self._fixture()
        sl = lists['one']
        sl.extend([1, 11])
        lists.add_to_list(12, sl)
        self.assertEqual(sl, [1, 11, 12])

    def test_speakers_on_different_lists(self):
        """ 2 have spoken before, 12 have spoken before. """
        lists = self._fixture()
        self._setup_meeting(lists.context, speaker_list_count=9)
        sl = lists['one']
        sl.speaker_log[2] = [5]
        sl.speaker_log[12] = [5]
        sl.extend([1])
        lists.add_to_list(12, sl)
        lists.add_to_list(11, sl)
        self.assertEqual(sl, [1, 11, 12])
        lists.add_to_list(3, sl)
        self.assertEqual(sl, [1, 11, 3, 12])
        lists.add_to_list(2, sl)
        self.assertEqual(sl, [1, 11, 3, 12, 2])
