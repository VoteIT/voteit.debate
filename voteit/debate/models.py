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
        assert name in self.speaker_lists
        self.context.__active_speaker_list__ = name

    def get_active_list(self):
        return self.speaker_lists.get(self.speaker_list_name, None)

    def active_ai(self, context):
        name = context.__name__
        if name not in self.speaker_lists:
            self.speaker_lists[name] = SpeakerList(title = context.title)
        self.set_active_list(name)
        return self.get_active_list()


class SpeakerList(Persistent):
    implements(ISpeakerList)

    def __init__(self, title = u""):
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
        self.speakers = PersistentList(value)

    def speaker_finished(self, name, seconds):
        name = int(name)
        self.remove(name)
        seconds = int(seconds)
        if name not in self.speaker_log:
            self.speaker_log[name] = PersistentList()
        self.speaker_log[name].append(seconds)

    def __repr__(self):
        return "<SpeakerList> '%s' with %s speakers" % (self.title, len(self.speakers))
