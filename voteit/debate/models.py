from zope.interface import implements
from zope.component import adapts
from persistent import Persistent
from persistent.list import PersistentList
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

    def set_active_list(self, name):
        assert name in self.speaker_lists
        self.context.__active_speaker_list__ = name

    def get_active_list(self):
        name = getattr(self.context, '__active_speaker_list__', None)
        return self.speaker_lists.get(name, None)

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
        self.speaker_log = OOBTree()
        self.current = None
        self.title = title

    def add(self, userid):
        self.speakers.append(userid)

    def remove(self, index):
        del self.speakers[index]

    def speaker_finished(self, seconds):
        userid = self.speakers.pop(0)
        seconds = int(seconds)
        if userid not in self.speaker_log:
            self.speaker_log[userid] = PersistentList()
        self.speaker_log[userid].append(seconds)

    def __repr__(self):
        return "<SpeakerList> '%s' with %s speakers" % (self.title, len(self.speakers))
