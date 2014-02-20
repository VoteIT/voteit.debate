from random import shuffle
from datetime import timedelta

from betahaus.pyracont.factories import createSchema
from zope.interface import implementer
from zope.component import adapter
from persistent import Persistent
from persistent.list import PersistentList
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from pyramid.traversal import find_interface
from pyramid.decorator import reify
from pyramid.threadlocal import get_current_registry
from pyramid.threadlocal import get_current_request
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting

from .interfaces import ISpeakerList
from .interfaces import ISpeakerLists
from .interfaces import ISpeakerListPlugin
from . import DebateTSF as _


@implementer(ISpeakerLists)
@adapter(IMeeting)
class SpeakerLists(object):
    """ See .interfaces.ISpeakerLists """

    def __init__(self, context):
        self.context = context

    def __nonzero__(self):
        return True #Otherwise this object will eval as false if no speaker lists are present

    @reify
    def _registry(self):
        return get_current_registry()

    @reify
    def speaker_list_plugin(self):
        return self.context.get_field_value('speaker_list_plugin', '')

    @property
    def speaker_lists(self):
        try:
            return self.context.__speaker_lists__
        except AttributeError:
            self.context.__speaker_lists__ = OOBTree()
            return self.context.__speaker_lists__

    @property
    def active_list_name(self, default = None):
        return getattr(self.context, '__active_speaker_list__', default)

    @active_list_name.setter
    def active_list_name(self, key):
        if key in self.speaker_lists or key is None:
            self.context.__active_speaker_list__ = key
            return key
        raise KeyError("No list named '%s'" % key)

    def add(self, key, value, parent = None):
        if not ISpeakerList.providedBy(value):
            raise TypeError("Only objects implementing ISpeakerList allowed")
        if parent is None:
            request = get_current_request()
            parent = request.context
        assert IAgendaItem.providedBy(parent)
        value.__parent__ = parent #To hack in traversal
        self.speaker_lists[key] = value
        return key

    def get(self, key, default = None):
        return key in self and self[key] or default

    def get_contexual_list_names(self, context):
        results = []
        for name in self.speaker_lists:
            if context.uid in name:
                results.append(name)
        def _sorter(obj):
            try:
                return int(obj.split("/")[1])
            except IndexError:
                return 0 #b/c compat
        return sorted(results, key = _sorter)

    def get_contextual_lists(self, context):
        return [self.get(x) for x in self.get_contexual_list_names(context)]

    def add_contextual_list(self, context):
        existing = self.get_contexual_list_names(context)
        if not existing:
            name = "%s/1" % context.uid
            title = context.title
        else:
            last_list = existing[-1]
            items = last_list.split("/")
            try:
                i = int(items[1]) + 1
            except IndexError: # pragma: no cover
                i = 1 #b/c compat
            name = "%s/%s" % (context.uid, i)
            title = "%s - %s" % (context.title, i)
        sl = SpeakerList(name, title = title)
        return self.add(name, sl, parent = context)

    def __getitem__(self, key): #dict api
        sl = self.speaker_lists[key]
        return self._registry.getAdapter(sl, ISpeakerListPlugin, name = self.speaker_list_plugin)

    def __setitem__(self, key, value): #dict api
        return self.add(key, value)

    def __delitem__(self, key): #dict api
        if self.active_list_name == key:
            self.active_list_name = None
        del self.speaker_lists[key]

    def __len__(self): #dict api
        return len(self.speaker_lists)

    def __contains__(self, key): #dict api
        return key in self.speaker_lists


_POSSIBLE_STATES = {u"open": _(u"Open"), u"closed": _(u"Closed")}


@implementer(ISpeakerListPlugin)
@adapter(ISpeakerList)
class SpeakerListPlugin(object):
    """ See .interfaces.ISpeakerListPlugin """
    plugin_name = u'default'
    plugin_title = _(u"Default list handler")
    plugin_description = u""
    __parent__ = None

    def __init__(self, context):
        self.context = context
        self.__parent__ = context.__parent__

    def __eq__(self, other):
        return self.plugin_name == getattr(other, 'plugin_name', None) and self.name == getattr(other, 'name', None)

    @property
    def name(self):
        return self.context.name

    @property
    def title(self):
        return self.context.title

    @title.setter
    def title(self, value):
        self.context.title = value

    @property
    def speakers(self):
        return self.context.speakers

    @property
    def speaker_log(self):
        return self.context.speaker_log

    @property
    def current(self):
        return self.context.current

    @current.setter
    def current(self, value):
        self.context.current = value

    @property
    def state(self):
        return self.context.state

    @state.setter
    def state(self, value):
        assert value in _POSSIBLE_STATES
        self.context.state = value

    @reify
    def settings(self):
        meeting = find_interface(self.context, IMeeting)
        assert meeting
        schema = createSchema('SpeakerListSettingsSchema')
        settings = dict(speaker_list_count = 1,
                        safe_positions = 0)
        settings.update(meeting.get_field_appstruct(schema))
        return settings

    def add(self, pn, override = False):
        assert isinstance(pn, int)
        if not override and self.state == u"closed":
            return
        if pn in self.speakers:
            return
        pos = self.get_position(pn)
        self.speakers.insert(pos, pn)

    def get_position(self, pn):
        use_lists = self.settings.get('speaker_list_count')
        safe_pos = self.settings.get('safe_positions')
        compare_val = self.get_number_for(pn)
        pos = len(self.speakers)
        for pn in reversed(self.speakers):
            if pos == safe_pos:
                break
            if compare_val >= self.get_number_for(pn):
                break
            pos -= 1
        return pos

    def get_stats(self, pn, format = True):
        if pn not in self.speaker_log:
            return (0, 0)
        time = sum(self.speaker_log[pn])
        if format:
            time = unicode(timedelta(seconds = time))
        return (len(self.speaker_log[pn]), time)

    def shuffle(self):
        use_lists = self.settings.get('speaker_list_count')
        lists = {}
        for speaker in self.speakers:
            cmp_val = len(self.speaker_log.get(speaker, ())) + 1
            if cmp_val > use_lists:
                cmp_val = use_lists
            cur = lists.setdefault(cmp_val, [])
            cur.append(speaker)
        del self.speakers[:]
        for i in range(1, use_lists + 1):
            if i in lists:
                shuffle(lists[i])
                self.speakers.extend(lists[i])

    def get_number_for(self, pn):
        assert isinstance(pn, int)
        use_lists = self.settings.get('speaker_list_count')
        cmp_val = len(self.speaker_log.get(pn, ())) + 1 #1 log entry means secondary speaker list - a val of 2
        return cmp_val <= use_lists and cmp_val or use_lists

    def speaker_active(self, pn):
        assert isinstance(pn, int)
        if pn in self.speakers:
            self.current = pn
            self.speakers.remove(pn)
            return pn

    def speaker_finished(self, pn, seconds):
        assert isinstance(pn, int)
        assert isinstance(seconds, int)
        if self.current != pn:
            return
        if self.current not in self.speaker_log:
            self.speaker_log[self.current] = PersistentList()
        self.speaker_log[self.current].append(seconds)
        self.current = None
        return pn

    def speaker_undo(self):
        if self.current == None:
            return
        self.speakers.insert(0, self.current)
        pn = self.current
        self.current = None
        return pn

    def get_state_title(self):
        return _POSSIBLE_STATES.get(self.state, u"")

    def __repr__(self): # pragma : no cover
        return "<%s> named '%s' adapting %s" % (self.__class__.__name__, self.name, self.context.__repr__())


@implementer(ISpeakerList)
class SpeakerList(Persistent):
    name = u""
    current = None
    title = u""
    state = u""
    __parent__ = None

    def __init__(self, name, title = u"", state = u"open"):
        self.name = name
        self.speakers = PersistentList()
        self.speaker_log = IOBTree()
        self.current = None
        self.title = title
        self.state = state

    def __repr__(self): # pragma : no cover
        return "<SpeakerList> '%s' with %s speakers" % (self.title.encode('utf-8'), len(self.speakers))


def get_speaker_list_plugins(request):
    return [(x.name, x.factory.plugin_title) for x in request.registry.registeredAdapters() if x.provided == ISpeakerListPlugin]

def includeme(config):
    config.registry.registerAdapter(SpeakerLists)
    config.registry.registerAdapter(SpeakerListPlugin)
