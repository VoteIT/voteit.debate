# -*- coding: utf-8 -*-
from UserDict import IterableUserDict
from datetime import timedelta
from random import shuffle

from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from persistent import Persistent

from arche.interfaces import IObjectUpdatedEvent
from arche.portlets import get_portlet_manager
from persistent.list import PersistentList
from pyramid.decorator import reify
from pyramid.interfaces import IRequest
from six import string_types
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from zope.component import adapter
from zope.interface import implementer

from voteit.debate.interfaces import ISpeakerList
from voteit.debate.interfaces import ISpeakerLists
from voteit.debate import _


@implementer(ISpeakerLists)
@adapter(IMeeting, IRequest)
class SpeakerLists(IterableUserDict):
    """ See .interfaces.ISpeakerLists """
    name = ""
    title = _("Default list handler")
    description = ""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def data(self):
        try:
            return self.context.__speaker_lists__
        except AttributeError:
            self.context.__speaker_lists__ = OOBTree()
            return self.context.__speaker_lists__

    @reify
    def settings(self):
#        schema = self.request.get_schema(context, context.type_name, 'edit', bind=None, event=True)
        from voteit.debate.schemas import SpeakerListSettingsSchema
        schema = SpeakerListSettingsSchema()
        #FIXME: use get_schema on request instead
        #Should map default values from schema
        settings = dict(speaker_list_count = 9,
                        safe_positions = 1)
        settings.update(self.context.get_field_appstruct(schema))
        return settings

    # @property
    # def active_list_name(self, default = None):
    #     return getattr(self.context, '__active_speaker_list__', default)
    #
    # @active_list_name.setter
    # def active_list_name(self, key):
    #     if key is None or key in self.speaker_lists:
    #         self.context.__active_speaker_list__ = key
    #         return key
    #     raise KeyError("No list named '%s'" % key)

    def get_list_names(self, uid):
        results = []
        for name in self:
            if uid in name:
                results.append(name)
        def _sorter(obj):
            try:
                return int(obj.split("/")[1])
            except IndexError:
                return 0 #b/c compat
        return sorted(results, key = _sorter)

    def get_lists_in(self, uid):
        return [self.get(x) for x in self.get_list_names(uid)]

    def add_list_to(self, context):
        assert IAgendaItem.providedBy(context)
        existing = self.get_list_names(context.uid)
        if not existing:
            key = "%s/1" % context.uid
            title = context.title
        else:
            last_list = existing[-1]
            items = last_list.split("/")
            try:
                i = int(items[1]) + 1
            except IndexError: # pragma: no cover
                i = 1 #b/c compat
            key = "%s/%s" % (context.uid, i)
            title = "%s - %s" % (context.title, i)
        sl = SpeakerList(key, title = title)
        sl.__parent__ = context
        self[key] = sl
        return sl

    def __setitem__(self, key, sl): #dict api
        if not ISpeakerList.providedBy(sl):
            raise TypeError("Only objects implementing ISpeakerList allowed")
        assert sl.__parent__ is not None
        self.data[key] = sl

    def __delitem__(self, key): #dict api
        if self.active_list_name == key:
            self.active_list_name = None
        del self.data[key]

    def __nonzero__(self):
        #Make sure the adapter registers as true even if it's empty
        return True

    def add_to_list(self, pn, sl, override = False):
        assert isinstance(pn, int)
        if not override and sl.state == "closed":
            return
        if pn in sl:
            return
        pos = self.get_position(pn, sl)
        sl.speakers.insert(pos, pn)

    def shuffle(self, sl):
        use_lists = self.settings.get('speaker_list_count')
        lists = {}
        for speaker in sl:
            cmp_val = len(sl.speaker_log.get(speaker, ())) + 1
            if cmp_val > use_lists:
                cmp_val = use_lists
            cur = lists.setdefault(cmp_val, [])
            cur.append(speaker)
        del sl.speakers[:]
        for i in range(1, use_lists + 1):
            if i in lists:
                shuffle(lists[i])
                sl.speakers.extend(lists[i])

    def get_position(self, pn, sl):
        safe_pos = self.settings.get('safe_positions')
        compare_val = self.get_list_number_for(pn, sl)
        pos = len(self)
        for speaker in reversed(sl):
            if pos == safe_pos:
                break
            if compare_val >= self.get_list_number_for(speaker, sl):
                break
            pos -= 1
        return pos

    def get_list_number_for(self, pn, sl):
        assert isinstance(pn, int)
        assert ISpeakerList.providedBy(sl)
        use_lists = self.settings.get('speaker_list_count')
        # 1 log entry means secondary speaker list - a val of 2
        cmp_val = len(sl.speaker_log.get(pn, ())) + 1
        return cmp_val <= use_lists and cmp_val or use_lists


@implementer(ISpeakerList)
class SpeakerList(Persistent):
    name = ""
    current = None
    title = ""
    state = ""
    __parent__ = None

    def __init__(self, name, title = "", state = "open"):
        self.name = name
        self.speakers = PersistentList()
        self.speaker_log = IOBTree()
        self.current = None
        self.title = title
        self.state = state

    def start(self, pn):
        assert isinstance(pn, int)
        if pn in self:
            self.current = pn
            self.speakers.remove(pn)
            return pn

    def finish(self, pn, seconds):
        if self.current != pn:
            return
        assert isinstance(pn, int)
        assert isinstance(seconds, int)
        if self.current not in self.speaker_log:
            self.speaker_log[self.current] = PersistentList()
        self.speaker_log[self.current].append(seconds)
        self.current = None
        return pn

    def undo(self):
        if self.current == None:
            return
        self.speakers.insert(0, self.current)
        pn = self.current
        self.current = None
        return pn

    def __repr__(self): # pragma : no cover
        return "<%s> '%s' with %s speakers" % (self.__class__.__name__, self.name, len(self.speakers))

    def __contains__(self, item):
        return item in self.speakers

    def __iter__(self):
        return iter(self.speakers)

    def __len__(self):
        return len(self.speakers)


def speaker_lists(request, meeting=None):
    """ Will fetch currently set ISpeakerLists adapter.
        Since this will be a cached property on the request object,
        the meeting argument is only for testing.
    """
    if not meeting:
        meeting = request.meeting
    return request.registry.getMultiAdapter([meeting, request], ISpeakerLists,
                                            name=meeting.speaker_list_plugin)


# def populate_from_proposals(sl, request = None):
#     if request is None:
#         request = get_current_request()
#     ai = find_interface(sl, IAgendaItem)
#     assert ai
#     meeting = find_interface(sl, IMeeting)
#     assert meeting
#     participant_numbers = request.registry.getAdapter(meeting, IParticipantNumbers)
#     handled_userids = set()
#     found = 0
#     for prop in ai.get_content(content_type = 'Proposal', states = ['published'], sort_on = 'created'):
#         userid = prop.creators[0]
#         if userid in handled_userids:
#             continue
#         handled_userids.add(userid)
#         pn = participant_numbers.userid_to_number.get(userid, None)
#         if not pn or pn in sl.speakers:
#             continue
#         sl.add(pn, override = True)
#         found += 1
#     return found


def insert_portlet_when_enabled(context, event):
    if event.changed and 'enable_voteit_debate' in event.changed:
        manager = get_portlet_manager(context)
        current = manager.get_portlets('agenda_item', 'voteit_debate')
        if not context.get_field_value('enable_voteit_debate', None):
            for portlet in current:
                manager.remove('agenda_item', portlet.uid)
        else:
            if not current:
                new_portlet = manager.add('agenda_item', 'voteit_debate')
                ai_slot = manager['agenda_item']
                current_order = list(ai_slot.keys())
                pos = current_order.index(new_portlet.uid)
                #Find a good position to insert it - above discussions or proposals
                types = ('ai_proposals', 'ai_discussions')
                for portlet in ai_slot.values():
                    if portlet.portlet_type in types:
                        pos = current_order.index(portlet.uid)
                        break
                current_order.remove(new_portlet.uid)
                current_order.insert(pos, new_portlet.uid)
                ai_slot.order = current_order


def includeme(config):
    config.add_request_method(speaker_lists, reify=True)
    # The default one won't have a name
    config.registry.registerAdapter(SpeakerLists, name=SpeakerLists.name)
    config.add_subscriber(insert_portlet_when_enabled, [IMeeting, IObjectUpdatedEvent])

    from voteit.core.models.meeting import Meeting
    #Bool property for enabled plugin
    def get_enable_voteit_debate(self):
        return self.get_field_value('enable_voteit_debate', None)
    def set_enable_voteit_debate(self, value):
        return self.set_field_value('enable_voteit_debate', bool(value))
    Meeting.enable_voteit_debate = property(get_enable_voteit_debate, set_enable_voteit_debate)

    #Property for adapter type
    def get_speaker_list_plugin(self):
        return self.get_field_value('speaker_list_plugin', '')
    def set_speaker_list_plugin(self, value):
        assert isinstance(value, string_types)
        self.set_field_value('speaker_list_plugin', value)
    Meeting.speaker_list_plugin = property(get_speaker_list_plugin, set_speaker_list_plugin)
