from zope.interface import implements
from zope.component import adapts
from persistent import Persistent
from persistent.list import PersistentList
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from voteit.core.models.interfaces import IMeeting

from .interfaces import ISpeakerListHandler
from .interfaces import ISpeakerList


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


class SpeakerList(Persistent):
    implements(ISpeakerList)

    def __init__(self, name, title = u""):
        self.name = name
        self.speakers = PersistentList()
        self.speaker_log = IOBTree()
        self.current = None
        self.title = title

    def add(self, name):
        name = int(name)
        if name not in self.speakers:
            self.speakers.append(name)

    def remove(self, name):
        name = int(name)
        self.speakers.remove(name)

    def set(self, value):
        self.speakers = PersistentList([int(x) for x in value])

    def speaker_finished(self, name, seconds):
        name = int(name)
        self.remove(name)
        seconds = int(seconds)
        if name not in self.speaker_log:
            self.speaker_log[name] = PersistentList()
        self.speaker_log[name].append(seconds)

    def __repr__(self):
        return "<SpeakerList> '%s' with %s speakers" % (self.title, len(self.speakers))
