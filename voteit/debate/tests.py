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

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerListHandler, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerListHandler, self._cut(None)))

    def test_integration(self):
        self.config.include('voteit.debate')
        meeting = Meeting()
        self.failUnless(self.config.registry.queryAdapter(meeting, ISpeakerListHandler))


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
        self.failUnless(verifyObject(ISpeakerList, self._cut()))

    def test_add(self):
        obj = self._cut()
        obj.add('jeff')
        self.assertIn('jeff', obj.speakers)

    def test_remove(self):
        obj = self._cut()
        obj.speakers.extend(['a', 'b', 'c'])
        obj.remove(1)
        self.assertNotIn('b', obj.speakers)

    def test_set(self):
        obj = self._cut()
        obj.speakers.extend(['a', 'b', 'c'])
        obj.set([1, 2 ,3])
        self.assertEqual((1, 2, 3,), tuple(obj.speakers))

    def test_speaker_finished(self):
        obj = self._cut()
        obj.speakers.extend(['a', 'b', 'c'])
        obj.speaker_finished(3)
        self.assertEqual(set(obj.speaker_log['a']), set([3]))
        self.assertNotIn('a', obj.speakers)

    def test_unicode_seconds_speaker_finished(self):
        obj = self._cut()
        obj.speakers.extend(['a', 'b', 'c'])
        obj.speaker_finished(u"4")
        self.assertEqual(set(obj.speaker_log['a']), set([4]))
