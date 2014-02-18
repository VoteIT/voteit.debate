import unittest

from pyramid import testing
from pyramid.traversal import find_interface
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.meeting import Meeting
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting

from .interfaces import ISpeakerList
from .interfaces import ISpeakerLists
from .interfaces import ISpeakerListPlugin


class SpeakerListsTests(unittest.TestCase):
    
    def setUp(self):
        request = testing.DummyRequest()
        request.context = AgendaItem()
        self.config = testing.setUp(request = request)

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from .models import SpeakerLists
        return SpeakerLists

    @property
    def _sl(self):
        from .models import SpeakerList
        return SpeakerList

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerLists, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerLists, self._cut(Meeting())))

    def test_get(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        obj = self._cut(meeting)
        obj['hello'] = self._sl('hello', title = "1")
        result = obj.get('hello')
        self.failUnless(result)
        self.failUnless(ISpeakerListPlugin.providedBy(result))

    def test_get_with_default_returns_default(self):
        default = object()
        meeting = Meeting()
        obj = self._cut(meeting)
        res = obj.get('404', default)
        self.assertEqual(res, default)

    def test_active_list(self):
        meeting = Meeting()
        obj = self._cut(meeting)
        obj['hello'] = self._sl('hello', title = "1")
        obj.active_list = 'hello'
        self.assertEqual(obj.active_list, 'hello')
        try:
            obj.active_list = '404'
            self.fail("KeyError not raised")
        except KeyError:
            pass

    def test_getitem_dict(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        obj = self._cut(meeting)
        obj['hello'] = sl = self._sl('hello', title = "1")
        self.assertNotEqual(obj['hello'], sl) #It's wrapped in the ISpeakerListPlugin adapter
        self.failUnless(ISpeakerListPlugin.providedBy(obj['hello']))

    def test_getitem_key_error(self):
        meeting = Meeting()
        obj = self._cut(meeting)
        try:
            obj['404']
            self.fail("Key error wasn't raised")
        except KeyError:
            pass

    def test_add_bad_object(self):
        meeting = Meeting()
        obj = self._cut(meeting)
        self.assertRaises(TypeError, obj.add, 'hello', object())

    def test_del(self):
        meeting = Meeting()
        obj = self._cut(meeting)
        obj['hello'] = self._sl('hello', title = "1")
        obj.active_list = 'hello'
        del obj['hello']
        self.assertEqual(obj.active_list, None)
        self.assertFalse('hello' in obj)

    def test_len(self):
        meeting = Meeting()
        obj = self._cut(meeting)
        obj['1'] = self._sl('1', title = "1")
        obj['2'] = self._sl('2', title = "1")        
        self.assertEqual(len(obj), 2)

    def test_get_contextual_lists(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        obj = self._cut(meeting)
        name = meeting.uid
        obj.speaker_lists[name] = self._sl(name, title = "1")
        name = "%s/2" % meeting.uid
        obj.speaker_lists[name] = self._sl(name, title = "2")
        name = "other"
        obj.speaker_lists[name] = self._sl(name, title = "other")
        results = obj.get_contextual_lists(meeting)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "1")

    def test_add_contextual_list(self):
        meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        obj = self._cut(meeting)
        for i in range(1, 12):
            obj.add_contextual_list(ai)
        self.assertEqual(len(obj.speaker_lists), 11)
        self.assertIn("%s/1" % ai.uid, obj.speaker_lists)
        self.assertIn("%s/11" % ai.uid, obj.speaker_lists)

    def test_get_contexual_list_names_sorts_correctly(self):
        meeting = Meeting()
        meeting['ai'] = ai = AgendaItem()
        obj = self._cut(meeting)
        for i in range(1, 12):
            obj.add_contextual_list(ai)
        result = obj.get_contexual_list_names(ai)
        self.assertEqual(len(result), 11)
        self.assertEqual("%s/1" % ai.uid, result[0])
        self.assertEqual("%s/11" % ai.uid, result[10])

    def test_integration(self):
        self.config.include('voteit.debate')
        meeting = Meeting()
        self.failUnless(self.config.registry.queryAdapter(meeting, ISpeakerLists))


class SpeakerListPluginTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp(request = testing.DummyRequest())

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from .models import SpeakerListPlugin
        return SpeakerListPlugin

    @property
    def _sl(self):
        from .models import SpeakerList
        return SpeakerList

    def _fixture(self, **kw):
        self.config.include('voteit.debate')
        meeting = Meeting()
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

    def test_integration(self):
        self.config.include('voteit.debate')
        sl = self._sl('hello')
        self.failUnless(self.config.registry.queryAdapter(sl, ISpeakerListPlugin))

    def test_settings(self):
        lists = self._fixture()
        obj = lists['uid/1']
        settings = obj.settings
        self.assertIn('speaker_list_count', settings)

    def test_traversal_works_on_adapter(self):
        lists = self._fixture()
        obj = lists['uid/1']
        self.failUnless(find_interface(obj, IMeeting))
        self.failUnless(find_interface(obj, IAgendaItem))

    def test_add(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.add(1)
        self.assertIn(1, obj.speakers)

    def test_add_with_secondary_speaker_list(self):
        lists = self._fixture(speaker_list_count = 2)
        obj = lists['uid/1']
        obj.add(1)
        obj.speaker_active(1)
        obj.speaker_finished(1, 10)
        obj.add(1)
        obj.add(2)
        self.assertEqual([2, 1], obj.speakers)

    def test_add_with_lots_of_speakers(self):
        lists = self._fixture(speaker_list_count = 3)
        obj = lists['uid/1']
        obj.speaker_log[1] = [1, 1, 1]
        obj.speaker_log[2] = [1]
        obj.speaker_log[3] = [1, 1]
        obj.speaker_log[4] = [1, 1, 1]
        obj.speaker_log[5] = [1]
        obj.speakers.extend([1, 2, 3, 4])
        obj.add(5)
        self.assertEqual(obj.speakers, [1, 2, 5, 3, 4])
        obj.add(6)
        self.assertEqual(obj.speakers, [6, 1, 2, 5, 3, 4])

    def test_add_with_one_in_log(self):
        lists = self._fixture(speaker_list_count = 2)
        obj = lists['uid/1']
        obj.speaker_log[1] = [1]
        obj.speakers.extend([2])
        obj.add(1)
        self.assertEqual(obj.speakers, [2, 1])

    def test_add_with_1_safe_pos_and_2_lists(self):
        lists = self._fixture(speaker_list_count = 2, safe_positions = 1)
        obj = lists['uid/1']
        obj.speaker_log[1] = [1]
        obj.speaker_log[2] = [1]
        obj.speakers.extend([1, 2])
        obj.add(3)
        self.assertEqual(obj.speakers, [1, 3, 2])

    def test_add_with_override(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.state = 'closed'
        obj.add(1)
        self.assertEqual(len(obj.speakers), 0)
        obj.add(1, override = True)
        self.assertEqual(len(obj.speakers), 1)

    def test_add_with_existing(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.add(1)
        self.assertEqual(len(obj.speakers), 1)
        obj.add(1)
        self.assertEqual(len(obj.speakers), 1)

    def test_get_stats_formated(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.speaker_log[1] = [3, 5, 2]
        self.assertEqual(obj.get_stats(1), (3, u'0:00:10'))
 
    def test_get_stats_int(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.speaker_log[1] = [3, 5, 2]
        self.assertEqual(obj.get_stats(1, format = None), (3, 10))

    def test_get_stats_nonexistent_user(self):
        lists = self._fixture()
        obj = lists['uid/1']
        self.assertEqual(obj.get_stats(1, format = None), (0, 0))

    def test_shuffle(self):
        lists = self._fixture()
        obj = lists['uid/1']
        ordered = range(0, 50)
        obj.speakers.extend(ordered)
        obj.shuffle()
        self.assertNotEqual(ordered, obj.speakers) #Yes this is a bad test since it might fail :P

    def test_shuffle_handle_serveral_lists(self):
        lists = self._fixture(speaker_list_count = 5)
        obj = lists['uid/1']
        obj.speaker_log[1] = []
        obj.speaker_log[2] = [1]
        obj.speaker_log[3] = [1, 1]
        obj.speaker_log[4] = [1, 1, 1]
        obj.speaker_log[5] = [1, 1, 1, 1]
        obj.speakers.extend([5, 4, 3, 2, 1])
        obj.shuffle()
        self.assertEqual(obj.speakers, [1, 2, 3, 4, 5])

    def test_get_number_for(self):
        lists = self._fixture(speaker_list_count = 2)
        obj = lists['uid/1']
        obj.speaker_log[1] = []
        obj.speaker_log[2] = [1]
        obj.speaker_log[3] = range(5)
        self.assertEqual(obj.get_number_for(1), 1)
        self.assertEqual(obj.get_number_for(2), 2)
        self.assertEqual(obj.get_number_for(3), 2)

    def test_speaker_finished(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.current = 3
        obj.speaker_finished(3, 5)
        self.assertIn(3, obj.speaker_log)
        self.assertEqual(obj.current, None)

    def test_speaker_finished_with_wrong_pn(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.current = 3
        obj.speaker_finished(1, 5)
        self.assertNotIn(1, obj.speaker_log)
        self.assertEqual(obj.current, 3)

    def test_speaker_undo(self):
        lists = self._fixture()
        obj = lists['uid/1']
        obj.speakers.extend([1, 3])
        obj.current = 2
        obj.speaker_undo()
        self.assertNotIn(2, obj.speaker_log)
        self.assertEqual(obj.speakers, [2, 1, 3])
        self.assertEqual(obj.current, None)

    def test_speaker_undo_nothing_to_do(self):
        lists = self._fixture(speaker_list_count = 2)
        obj = lists['uid/1']
        obj.speakers.extend([1, 3])
        obj.speaker_undo()
        self.assertEqual(obj.speakers, [1, 3])


class SpeakerListTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from .models import SpeakerList
        return SpeakerList

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerList, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerList, self._cut('Hello world')))
