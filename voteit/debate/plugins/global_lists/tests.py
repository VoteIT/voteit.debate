import unittest

from pyramid import testing
from pyramid.request import apply_request_extensions
from voteit.core.models.agenda_item import AgendaItem
from voteit.irl.models.interfaces import IParticipantNumbers
from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject
from voteit.core.models.meeting import Meeting

from voteit.debate.interfaces import ISpeakerListSettings
from voteit.debate.interfaces import ISpeakerLists


class GlobalListsTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('arche.testing')
        self.config.include('voteit.core.helpers')
        self.config.include('voteit.debate.schemas')
        self.config.include('voteit.debate.models')
        self.config.include('voteit.debate.plugins.global_lists')

    def tearDown(self):
        testing.tearDown()

    @property
    def _cut(self):
        from voteit.debate.plugins.global_lists.models import GlobalLists
        return GlobalLists

    def _request(self, **kw):
        request = testing.DummyRequest(**kw)
        apply_request_extensions(request)
        self.config.begin(request)
        return request

    def _setup_meeting(self, meeting, speaker_list_count=1, safe_positions=0, **kw):
        settings = ISpeakerListSettings(meeting)
        settings.update(
            speaker_list_plugin='global_lists',
            speaker_list_count=speaker_list_count,
            safe_positions=safe_positions,
            global_time_restrictions=[3,2,1],
            **kw)
        return settings

    def _fixture(self):
        meeting = Meeting()
        self._setup_meeting(meeting)
        request = self._request()
        request.meeting = meeting
        return meeting, request

    @property
    def _sl(self):
        from voteit.debate.models import SpeakerList
        return SpeakerList

    def test_verify_class(self):
        self.failUnless(verifyClass(ISpeakerLists, self._cut))

    def test_verify_object(self):
        meeting, request = self._fixture()
        self.failUnless(verifyObject(ISpeakerLists, self._cut(meeting, request)))

    def test_add_to_list_default_settings(self):
        # Test same thing as default speaker list
        meeting, request = self._fixture()
        obj = self._cut(meeting, request)
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
        # No exceptions on double add
        obj.add_to_list(2, sl, override=True)
        # No exception on add when speaker is current
        sl.start(2)
        self.assertNotIn(2, sl)
        obj.add_to_list(2, sl, override=True)
        self.assertNotIn(2, sl)

    def test_remove_from_list_default_settings(self):
        meeting, request = self._fixture()
        obj = self._cut(meeting, request)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        obj.add_to_list(1, sl)
        self.assertIn(1, sl)
        obj.remove_from_list(1, sl)
        self.assertNotIn(1, sl)

    def test_get_total_count(self):
        meeting, request = self._fixture()
        obj = self._cut(meeting, request)

        ai1 = AgendaItem()
        ai2 = AgendaItem()

        sl1 = obj.add_list_to(ai1)
        sl2 = obj.add_list_to(ai2)

        sl1.speaker_log[1] = [60, 120]
        sl2.speaker_log[1] = [60, 120]
        sl2.speaker_log[2] = [60]

        result = obj.total_count([1, 2])
        self.assertEqual(4, result[1])
        self.assertEqual(1, result[2])

    def test_get_available_restrictions(self):
        meeting, request = self._fixture()
        request.params['timeRestriction'] = 3
        obj = self._cut(meeting, request)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        self.assertEqual([3, 2, 1], obj.get_available_restrictions(1))
        obj.add_to_list(1, sl)
        self.assertIn(1, sl)
        self.assertEqual([2, 1], obj.get_available_restrictions(1))

    def test_get_time_restriction(self):
        meeting, request = self._fixture()
        request.params['timeRestriction'] = 3
        obj = self._cut(meeting, request)
        sl = self._sl('one')
        sl.__parent__ = meeting
        obj['one'] = sl
        self.assertEqual(None, obj.get_time_restriction(sl, 1))
        obj.add_to_list(1, sl)
        self.assertEqual(3, obj.get_time_restriction(sl, 1))

    def test_get_available_restrictions_from_currently_authenticated(self):
        self.config.testing_securitypolicy(userid='jane')
        self.config.include('voteit.irl.models.participant_numbers')
        meeting, request = self._fixture()
        pns = IParticipantNumbers(meeting)
        pns.new_tickets('admin', 1)
        ticket = pns.tickets[1]
        # 'jane' should now be participant nr 1
        pns.claim_ticket('jane', ticket.token)
        self.assertEqual('jane', request.authenticated_userid)
        obj = self._cut(meeting, request)
        self.assertEqual([3, 2, 1], obj.get_available_restrictions())
        ai = AgendaItem()
        sl = obj.add_list_to(ai)
        obj.add_to_list(1, sl)
        self.assertEqual([2, 1], obj.get_available_restrictions())

    def test_remove_from_list_w_active(self):
        meeting, request = self._fixture()
        request.params['timeRestriction'] = 3
        obj = self._cut(meeting, request)
        ai = AgendaItem()
        sl = obj.add_list_to(ai)
        self.assertEqual([3, 2, 1], obj.get_available_restrictions(1))
        self.assertEqual(None, obj.get_time_restriction(sl, 1))
        obj.add_to_list(1, sl)
        self.assertEqual([2, 1], obj.get_available_restrictions(1))
        self.assertEqual(3, obj.get_time_restriction(sl, 1))
        obj.remove_from_list(1, sl)
        self.assertEqual([3, 2, 1], obj.get_available_restrictions(1))
        self.assertEqual(None, obj.get_time_restriction(sl, 1))

    def test_finish_on_list(self):
        meeting, request = self._fixture()
        request.params['timeRestriction'] = 3
        obj = self._cut(meeting, request)
        ai = AgendaItem()
        sl = obj.add_list_to(ai)
        obj.add_to_list(1, sl)
        self.assertEqual([2, 1], obj.get_available_restrictions(1))
        self.assertEqual(3, obj.get_time_restriction(sl, 1))
        sl.start(1)
        obj.finish_on_list(sl)
        self.assertEqual([2, 1], obj.get_available_restrictions(1))
        self.assertEqual(None, obj.get_time_restriction(sl, 1))

    def test_list_deleted_w_active_speaker(self):
        meeting, request = self._fixture()
        request.params['timeRestriction'] = 3
        obj = self._cut(meeting, request)
        ai = AgendaItem()
        sl = obj.add_list_to(ai)
        obj.add_to_list(1, sl)
        self.assertEqual([2, 1], obj.get_available_restrictions(1))
        self.assertEqual(3, obj.get_time_restriction(sl, 1))
        sl.start(1)
        del obj[sl.name]
        # Everything should be restored
        self.assertEqual([3, 2, 1], obj.get_available_restrictions(1))
        self.assertEqual(None, obj.get_time_restriction(sl, 1))

    def test_list_deleted_w_speaker_in_list(self):
        meeting, request = self._fixture()
        request.params['timeRestriction'] = 3
        obj = self._cut(meeting, request)
        ai = AgendaItem()
        sl = obj.add_list_to(ai)
        obj.add_to_list(1, sl)
        self.assertEqual([2, 1], obj.get_available_restrictions(1))
        self.assertEqual(3, obj.get_time_restriction(sl, 1))
        del obj[sl.name]
        self.assertEqual([3, 2, 1], obj.get_available_restrictions(1))
        self.assertEqual(None, obj.get_time_restriction(sl, 1))
