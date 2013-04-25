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

    def test_speaker_finished(self):
        obj = self._cut('n')
        obj.speakers.extend([1, 2, 3])
        obj.speaker_finished(2, 3)
        self.assertEqual(set(obj.speaker_log[2]), set([3]))
        self.assertNotIn(2, obj.speakers)

    def test_unicode_seconds_speaker_finished(self):
        obj = self._cut('n')
        obj.speakers.extend(['a', 'b', 'c', 12])
        obj.speaker_finished(12, u"4")
        self.assertEqual(set(obj.speaker_log[12]), set([4]))
