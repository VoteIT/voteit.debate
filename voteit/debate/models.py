# -*- coding: utf-8 -*-
from UserDict import IterableUserDict
from UserList import UserList
from calendar import timegm
from datetime import timedelta
from random import shuffle

from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from persistent import Persistent

from arche.interfaces import IObjectUpdatedEvent
from arche.portlets import get_portlet_manager
from arche.utils import AttributeAnnotations
from arche.utils import utcnow
from persistent.list import PersistentList
from pyramid.decorator import reify
from pyramid.interfaces import IRequest
from pyramid.renderers import render
from six import string_types
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.irl.models.interfaces import IParticipantNumbers
from zope.component import adapter
from zope.interface import implementer

from voteit.debate.interfaces import ISpeakerList, ISpeakerListSettings
from voteit.debate.interfaces import ISpeakerLists
from voteit.debate import _


@implementer(ISpeakerLists)
@adapter(IMeeting, IRequest)
class SpeakerLists(IterableUserDict):
    """ See .interfaces.ISpeakerLists """
    name = ""
    title = _("Default list handler")
    description = ""
    state_titles = {"open": _("Open"), "closed": _("Closed")}
    templates = {
        'speaker': 'voteit.debate:templates/speaker_item.pt',
        'log': 'voteit.debate:templates/speaker_log_item.pt',
        'fullscreen': 'voteit.debate:templates/speaker_item_fullscreen.pt',
        'user': 'voteit.debate:templates/speaker_item_user.pt',
    }

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def data(self):
        try:
            return self.context._speaker_lists
        except AttributeError:
            self.context._speaker_lists = OOBTree()
            return self.context._speaker_lists

    @reify
    def settings(self):
#        schema = self.request.get_schema(context, context.type_name, 'edit', bind=None, event=True)
        #from voteit.debate.schemas import SpeakerListSettingsSchema
        #schema = SpeakerListSettingsSchema()
        #FIXME: use get_schema on request instead
        #Should map default values from schema

        #Fallback to default class
        settings = dict(ISpeakerListSettings(self.context, SpeakerListSettings(self.context)))
        settings.setdefault('speaker_list_count', 9)
        settings.setdefault('safe_positions',1)
        return settings

    def set_active_list(self, list_name, category='default'):
        try:
            assert list_name in self
        except AssertionError:
            raise KeyError("No list named %r" % list_name)
        try:
            active = self.context._v_active_lists
        except AttributeError:
            active = self.context._v_active_lists = OOBTree()
        active[category] = list_name

    def get_active_list(self, category='default'):
        return getattr(self.context, '_v_active_lists', {}).get(category, '')

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

    def get_state_title(self, sl, translate=True):
        title = self.state_titles.get(sl.state, '')
        if translate:
            return self.request.localizer.translate(title)
        return title

    def add_to_list(self, pn, sl, override = False):
        assert isinstance(pn, int)
        if not override and sl.state == "closed":
            return
        if pn in sl:
            return
        pos = self.get_position(pn, sl)
        sl.insert(pos, pn)
        return pos

    def shuffle(self, sl):
        use_lists = self.settings.get('speaker_list_count')
        lists = {}
        for speaker in sl:
            cmp_val = len(sl.speaker_log.get(speaker, ())) + 1
            if cmp_val > use_lists:
                cmp_val = use_lists
            cur = lists.setdefault(cmp_val, [])
            cur.append(speaker)
        del sl[:]
        for i in range(1, use_lists + 1):
            if i in lists:
                shuffle(lists[i])
                sl.extend(lists[i])

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

    def render_tpl(self, name, **kw):
        return render(self.templates[name], kw, request=self.request)

    # def render_speaker_item(self, pn, sl, controls=True):
    #     safe_positions = self.settings['safe_positions']
    #     userid = self._pn_to_userid.get(pn, None)
    #     response = dict(
    #         sl=sl,
    #         pn=pn,
    #         userid=userid,
    #         is_active=pn == sl.current,
    #         is_locked=pn in sl and sl.index(pn) < safe_positions,
    #         controls=controls and self.request.is_moderator,
    #     )
    #     return render(self.speaker_tpl, response, request=self.request)

    @reify
    def _pn_to_userid(self):
        return IParticipantNumbers(self.context).number_to_userid


@implementer(ISpeakerListSettings)
@adapter(IMeeting)
class SpeakerListSettings(AttributeAnnotations):
    attr_name = '_voteit_debate_settings'


@implementer(ISpeakerList)
class SpeakerList(PersistentList):
    name = ""
    title = ""
    state = ""
    __parent__ = None

    def __init__(self, name, title = "", state = "open"):
        super(SpeakerList, self).__init__()
        self.name = name
        self.speaker_log = IOBTree()
        self.title = title
        self.state = state

    @property
    def current(self):
        return getattr(self, '_v_current', None)
    @current.setter
    def current(self, value):
        self._v_current = value

    @property
    def current_secs(self):
        try:
            if self._v_start_ts is not None:
                ts = utcnow() - self._v_start_ts
                return ts.seconds
        except AttributeError:
            pass

    @property
    def start_ts_epoch(self):
        start_ts = getattr(self, '_v_start_ts', None)
        if start_ts:
            return timegm(start_ts.timetuple())

    def open(self):
        return self.state == 'open'

    def start(self, pn):
        assert isinstance(pn, int)
        if pn in self:
            self.current = pn
            self.remove(pn)
            self._v_start_ts = utcnow()
            return pn

    def finish(self, pn):
        if self.current != pn:
            return
        assert isinstance(pn, int)
        if self.current not in self.speaker_log:
            self.speaker_log[self.current] = PersistentList()
        # While this is a volatile attr, current is also volatile.
        # So if it doesn't exist, neither will current!
        self.speaker_log[self.current].append(self.current_secs)
        self._v_start_ts = None
        self.current = None
        return pn

    def undo(self):
        if self.current == None:
            return
        self.insert(0, self.current)
        pn = self.current
        self.current = None
        self._v_start_ts = None
        return pn

    def __repr__(self): # pragma : no cover
        return "<%s> '%s' with %s speakers" % (self.__class__.__name__, self.name, len(self))


def speaker_lists(request, meeting=None):
    """ Will fetch currently set ISpeakerLists adapter.
        Since this will be a cached property on the request object,
        the meeting argument is only for testing.
    """
    if not meeting:
        meeting = request.meeting
    name = ISpeakerListSettings(meeting, {}).get('speaker_list_plugin', '')
    return request.registry.getMultiAdapter([meeting, request], ISpeakerLists,
                                            name=name)


def includeme(config):
    config.add_request_method(speaker_lists, reify=True)
    # The default one won't have a name
    config.registry.registerAdapter(SpeakerLists, name=SpeakerLists.name)
    config.registry.registerAdapter(SpeakerListSettings)

 #   config.add_subscriber(insert_portlet_when_enabled, [IMeeting, IObjectUpdatedEvent])
