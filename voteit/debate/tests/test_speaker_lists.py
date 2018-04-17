# -*- coding: utf-8 -*-
import unittest

from pyramid import testing
from pyramid.request import apply_request_extensions
from pyramid.traversal import find_interface
from voteit.core.models.agenda_item import AgendaItem
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.meeting import Meeting
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject

from voteit.debate.interfaces import ISpeakerLists, ISpeakerListSettings


class SpeakerListsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        self.config.include('voteit.debate.schemas')
        self.request = testing.DummyRequest()
        apply_request_extensions(self.request)
        self.config.begin(self.request)

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.debate.models import SpeakerLists
        return SpeakerLists

    @property
    def _sl(self):
        from voteit.debate.models import SpeakerList
        return SpeakerList

    def _mk_one(self, context=None):
        if context is None:
            context = testing.DummyResource()
        return self._cut(context, self.request)

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerLists, self._cut))

    def test_verify_object(self):
        self.failUnless(verifyObject(ISpeakerLists, self._cut(Meeting(), self.request)))

    def test_get_list_names(self):
        obj = self._mk_one()
        sl1 = self._sl('one')
        sl1.__parent__ = testing.DummyResource()
        obj['one/1'] = sl1
        self.assertEqual(obj.get_list_names('one'), ['one/1'])
        self.assertEqual(obj.get_list_names('two'), [])

    def test_get_lists_in(self):
        obj = self._mk_one()
        sl1 = self._sl('one')
        sl1.__parent__ = testing.DummyResource()
        obj['one/1'] = sl1
        self.assertEqual(obj.get_lists_in('one'), [sl1])
        self.assertEqual(obj.get_lists_in('two'), [])

    def test_add_list_to(self):
        obj = self._mk_one()
        ai = AgendaItem(uid = 'one')
        sl = obj.add_list_to(ai)
        self.assertEqual(sl.__parent__, ai)
        self.assertIn(sl, obj.get_lists_in(ai.uid))
        sl2 = obj.add_list_to(ai)
        self.assertTrue('/2' in sl2.name)

    def test_get_state_title(self):
        obj = self._mk_one()
        sl = self._sl('name')
        self.assertEqual(obj.get_state_title(sl), 'Open')
        sl.state = 'closed'
        self.assertEqual(obj.get_state_title(sl), 'Closed')

    def test_settings_takes_default_from_schema(self):
        obj = self._mk_one()
        self.assertEqual(obj.settings['speaker_list_count'], 9)

    def test_set_active_list(self):
        obj = self._mk_one()
        self.assertRaises(KeyError, obj.set_active_list, 'dont exist')
        sl = self._sl('one')
        sl.__parent__ = testing.DummyResource()
        obj['one'] = sl
        obj.set_active_list('one')
        self.assertEqual(obj.get_active_list(), 'one')

    def test_del_active_list(self):
        obj = self._mk_one()
        sl = self._sl('one')
        sl.__parent__ = testing.DummyResource()
        obj['one'] = sl
        obj.set_active_list('one')
        obj.del_active_list()
        self.assertFalse(obj.get_active_list())

    def test_active_list_deleted(self):
        obj = self._mk_one()
        sl = self._sl('one')
        sl.__parent__ = testing.DummyResource()
        obj['one'] = sl
        obj.set_active_list('one')
        del obj['one']
        self.assertFalse(obj.get_active_list())

    def test_active_list_poped(self):
        obj = self._mk_one()
        sl = self._sl('one')
        sl.__parent__ = testing.DummyResource()
        obj['one'] = sl
        obj.set_active_list('one')
        obj.pop('one')
        self.assertFalse(obj.get_active_list())

    def test_emtpy_handler_is_truthy(self):
        obj = self._mk_one()
        self.assertTrue(bool(obj))

    def test_get_state_title(self):
        obj = self._mk_one()
        sl = self._sl('one')
        sl.__parent__ = testing.DummyResource()
        obj['one'] = sl
        self.assertEqual(obj.get_state_title(sl), 'Open')
        self.assertEqual(obj.get_state_title(sl, translate=False), 'Open')

    def test_add_to_list_default_settings(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        obj = self._mk_one(meeting)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        obj.add_to_list(1, sl)
        self.assertIn(1, sl)
        sl.state = 'closed'
        obj.add_to_list(2, sl)
        self.assertNotIn(2, sl)
        obj.add_to_list(2, sl, override=True)
        self.assertIn(2, sl)
        #No exceptions on double add
        obj.add_to_list(2, sl, override=True)
        #No exception on add when speaker is current
        sl.start(2)
        self.assertNotIn(2, sl)
        obj.add_to_list(2, sl, override=True)
        self.assertNotIn(2, sl)

    def test_shuffle(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        obj = self._mk_one(meeting)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        for i in range(100):
            obj.add_to_list(i, sl)
        original = list(sl)
        obj.shuffle(sl)
        self.assertNotEqual(original, list(sl))

    def test_get_list_number_for(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        settings = ISpeakerListSettings(meeting)
        settings['speaker_list_count'] = 1
        settings['safe_positions'] = 0
        obj = self._mk_one(meeting)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        sl.extend(range(3))
        self.assertEqual(obj.get_list_number_for(4, sl), 1)

    def test_get_position_one_list(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        settings = ISpeakerListSettings(meeting)
        settings['speaker_list_count'] = 1
        settings['safe_positions'] = 0
        obj = self._mk_one(meeting)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        sl.extend(range(3))
        self.assertEqual(obj.get_position(3, sl), 3)
        obj.add_to_list(3, sl)
        self.assertEqual(list(sl), [0,1,2,3])

    def test_get_position_safe_pos(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        settings = ISpeakerListSettings(meeting)
        settings['speaker_list_count'] = 2
        settings['safe_positions'] = 1
        obj = self._mk_one(meeting)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        sl.append(1)
        sl.append(2)
        sl.append(3)
        sl.speaker_log[1] = [5, 5]
        sl.speaker_log[2] = [5, 5]
        sl.speaker_log[3] = [5, 5]
        obj.add_to_list(4, sl)
        self.assertEqual(list(sl), [1,4,2,3])
        self.assertEqual(obj.get_position(4, sl), 2)

    def test_get_position_several_lists(self):
        self.config.include('voteit.debate.models')
        meeting = Meeting()
        settings = ISpeakerListSettings(meeting)
        settings['speaker_list_count'] = 9
        settings['safe_positions'] = 1
        obj = self._mk_one(meeting)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        sl.append(1)
        sl.append(2)
        sl.append(3)
        sl.append(4)
        sl.speaker_log[1] = [1]
        sl.speaker_log[2] = [2, 2]
        sl.speaker_log[3] = [3, 3, 3]
        sl.speaker_log[4] = [4, 4, 4, 4]
        sl.speaker_log[5] = [5, 5]
        self.assertEqual(obj.get_position(5, sl), 2)
        obj.add_to_list(5, sl)
        self.assertEqual(list(sl), [1,2,5,3,4])
