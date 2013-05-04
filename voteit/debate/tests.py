import unittest

from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from voteit.core.models.meeting import Meeting

from .interfaces import ISpeakerList
from .interfaces import ISpeakerListHandler


class SpeakerListHandlerTests(unittest.TestCase):
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    @property
    def _cut(self):
        from .models import SpeakerListHandler
        return SpeakerListHandler

    @property
    def _sl(self):
        from .models import SpeakerList
        return SpeakerList

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerListHandler, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerListHandler, self._cut(None)))

    def test_integration(self):
        self.config.include('voteit.core.models.js_util')
        self.config.include('voteit.debate')
        meeting = Meeting()
        self.failUnless(self.config.registry.queryAdapter(meeting, ISpeakerListHandler))

    def test_get_contextual_lists(self):
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
        obj = self._cut(meeting)
        obj.add_contextual_list(meeting)
        self.assertEqual(len(obj.speaker_lists), 1)
        obj.add_contextual_list(meeting)
        self.assertEqual(len(obj.speaker_lists), 2)
        obj.add_contextual_list(meeting)
        self.assertEqual(len(obj.speaker_lists), 3)
        results = obj.get_contextual_lists(meeting)
        self.assertEqual(results[-1].name, "%s/3" % meeting.uid)

    def test_remove_list(self):
        meeting = Meeting()
        obj = self._cut(meeting)
        obj.add_contextual_list(meeting)
        obj.remove_list(meeting.uid)
        self.assertEqual(len(obj.speaker_lists), 0)


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
        self.failUnless(verifyObject(ISpeakerList, self._cut('n')))

    def test_add(self):
        obj = self._cut('n')
        obj.add(1)
        self.assertIn(1, obj.speakers)

    def test_add_string(self):
        obj = self._cut('n')
        obj.add("1")
        self.assertIn(1, obj.speakers)

    def test_add_with_secondary_speaker_list(self):
        obj = self._cut('n')
        obj.add(1)
        obj.speaker_active(1)
        obj.speaker_finished(10)
        obj.add(1)
        obj.add(2, use_lists = 2)
        self.assertEqual([2, 1], obj.speakers)

    def test_add_with_lots_of_speakers(self):
        obj = self._cut('n')
        obj.speaker_log[1] = [1, 1, 1]
        obj.speaker_log[2] = [1]
        obj.speaker_log[3] = [1, 1]
        obj.speaker_log[4] = [1, 1, 1]
        obj.speaker_log[5] = [1]
        obj.speakers.extend([1, 2, 3, 4])
        obj.add(5, 3)
        self.assertEqual(obj.speakers, [1, 2, 5, 3, 4])
        obj.add(6, 3)
        self.assertEqual(obj.speakers, [6, 1, 2, 5, 3, 4])

    def test_add_with_one_in_log(self):
        obj = self._cut('n')
        obj.speaker_log[1] = [1]
        obj.speakers.extend([2])
        obj.add(1, use_lists = 2)
        self.assertEqual(obj.speakers, [2, 1])

    def test_remove(self):
        obj = self._cut('n')
        obj.speakers.extend([1, 2, 3])
        obj.remove(2)
        self.assertNotIn(2, obj.speakers)

    def test_set(self):
        obj = self._cut('n')
        obj.speakers.extend([1, 2, 3])
        obj.set([1, 2 ,3])
        self.assertEqual((1, 2, 3,), tuple(obj.speakers))

    def test_speaker_active(self):
        obj = self._cut('n')
        obj.speakers.extend([1, 2, 3])
        obj.speaker_active(1)
        self.assertEqual(obj.current, 1)
        self.assertEqual(obj.speakers, [2, 3])

    def test_speaker_finished(self):
        obj = self._cut('n')
        obj.speakers.extend([1, 3])
        obj.current = 2
        obj.speaker_finished(3)
        self.assertEqual(set(obj.speaker_log[2]), set([3]))
        self.assertNotIn(2, obj.speakers)

    def test_unicode_seconds_speaker_finished(self):
        obj = self._cut('n')
        obj.current = 12
        obj.speaker_finished(4)
        self.assertEqual(set(obj.speaker_log[12]), set([4]))
