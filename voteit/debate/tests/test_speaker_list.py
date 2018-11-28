# -*- coding: utf-8 -*-
import unittest

from arche.utils import utcnow
from datetime import timedelta
from pyramid import testing
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.debate.interfaces import ISpeakerList


class SpeakerListTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.debate.models import SpeakerList
        return SpeakerList

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerList, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerList, self._cut('Hello world')))

    def test_start(self):
        obj = self._cut('name')
        obj.append(1)
        obj.start(1)
        self.assertNotIn(1, obj)
        self.assertEqual(1, obj.current)

    def test_finish(self):
        obj = self._cut('name')
        obj.append(1)
        obj.start(1)
        obj.start_ts = utcnow() - timedelta(seconds=10)
        obj.finish(1)
        self.assertEqual(obj.current, None)
        self.assertEqual(sum(obj.speaker_log[1]), 10)

    def test_finish_not_ongoing(self):
        obj = self._cut('name')
        obj.append(1)
        obj.finish(1)
        self.assertEqual(obj.current, None)
        self.assertNotIn(1, obj.speaker_log)
        self.assertIn(1, obj)

    def test_undo(self):
        obj = self._cut('name')
        obj.append(2)
        obj.append(1)
        obj.start(1)
        self.assertEqual(obj.undo(), 1)
        self.assertEqual(list(obj), [1, 2])
        self.assertEqual(obj.current, None)
        #Double-fire has no effect
        self.assertEqual(obj.undo(), None)

    def test_list_behaviour(self):
        obj = self._cut('name')
        obj.extend([1,2,3])
        self.assertEqual(list(obj), [1,2,3])
        self.assertEqual(list(reversed(obj)), [3,2,1])

    def test_chronological_migrates_automatically(self):
        obj = self._cut('name')
        # Make it look like old data
        obj.data.extend([1,2,3])
        self.assertEqual(len(obj), 3)
        self.assertEqual(len(obj.chronological), 3)
