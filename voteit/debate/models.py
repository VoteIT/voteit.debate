from random import shuffle

from zope.interface import implements
from zope.component import adapts
from persistent import Persistent
from persistent.list import PersistentList
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from voteit.core.models.interfaces import IMeeting

from .interfaces import ISpeakerListHandler
from .interfaces import ISpeakerList
from . import DebateTSF as _


class SpeakerListHandler(object):
    """ See .interfaces.ISpeakerListHandler """
    implements(ISpeakerListHandler)
    adapts(IMeeting)

    def __init__(self, context):
        self.context = context

    @property
    def speaker_lists(self):
        try:
            return self.context.__speaker_lists__
        except AttributeError:
            self.context.__speaker_lists__ = OOBTree()
            return self.context.__speaker_lists__

    @property
    def speaker_list_name(self):
        return getattr(self.context, '__active_speaker_list__', None)

    def set_active_list(self, name):
        self.context.__active_speaker_list__ = name

    def get_active_list(self):
        return self.speaker_lists.get(self.speaker_list_name, None)

    def get_contextual_lists(self, context):
        results = []
        for name in self.speaker_lists:
            if name == context.uid or name.startswith("%s/" % context.uid):
                results.append(name)
        return [self.speaker_lists[x] for x in sorted(results)]

    def add_contextual_list(self, context):
        existing = self.get_contextual_lists(context)
        if not existing:
            name = context.uid
            title = context.title
        else:
            last_list = existing[-1]
            items = last_list.name.split("/")
            if len(items) == 1:
                i = 2
            else:
                i = int(items[1]) + 1
            name = "%s/%s" % (context.uid, i)
            title = "%s - %s" % (context.title, i)
        self.speaker_lists[name] = SpeakerList(name, title = title)

    def remove_list(self, name):
        if self.speaker_list_name == name:
            self.set_active_list(None)
        del self.speaker_lists[name]


_POSSIBLE_STATES = {u"open": _(u"Open"), u"closed": _(u"Closed")}


class SpeakerList(Persistent):
    implements(ISpeakerList)
    name = u""
    current = None
    title = u""
    state = u""

    def __init__(self, name, title = u"", state = u"open"):
        self.name = name
        self.speakers = PersistentList()
        self.speaker_log = IOBTree()
        self.current = None
        self.title = title
        self.set_state(state)

    def get_expected_pos(self, name, use_lists = 1, safe_pos = 0):
        assert int(use_lists) #0 is not an okay value either
        def _compare_val(pn):
            n = len(self.speaker_log.get(pn, ())) + 1
            return n < use_lists and n or use_lists
        compare_val = _compare_val(name)
        pos = len(self.speakers)
        for pn in reversed(self.speakers):
            if pos == safe_pos:
                break
            if compare_val >= _compare_val(pn):
                break
            pos -= 1
        return pos

    def add(self, name, use_lists = 1, safe_pos = 0, override = False):
        assert int(use_lists) #0 is not an okay value either
        if not override and self.state == u"closed":
            return
        name = int(name)
        if name in self.speakers:
            return
        pos = self.get_expected_pos(name, use_lists = use_lists, safe_pos = safe_pos)
        self.speakers.insert(pos, name)

    def remove(self, name):
        name = int(name)
        if name in self.speakers:
            self.speakers.remove(name)

    def set(self, value):
        self.speakers = PersistentList([int(x) for x in value])

    def speaker_active(self, name):
        name = int(name)
        if name in self.speakers:
            self.current = name
            self.remove(name)
        else:
            self.current = None

    def speaker_finished(self, seconds):
        if self.current == None:
            return
        seconds = int(seconds)
        if self.current not in self.speaker_log:
            self.speaker_log[self.current] = PersistentList()
        self.speaker_log[self.current].append(seconds)
        self.current = None

    def speaker_undo(self):
        if self.current == None:
            return
        self.speakers.insert(0, self.current)
        self.current = None

    def set_state(self, state):
        assert state in _POSSIBLE_STATES
        self.state = state

    def get_state_title(self):
        return _POSSIBLE_STATES.get(self.state, u"")

    def shuffle(self):
        shuffle(self.speakers)

    def __repr__(self):
        return "<SpeakerList> '%s' with %s speakers" % (self.title, len(self.speakers))
