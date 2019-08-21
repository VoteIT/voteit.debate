# -*- coding: utf-8 -*-

# Events for common list operations like start, finish etc


class SpeakerListUpdatedEvent(object):
    def __init__(self, context, request, pn=None):
        self.context = context
        self.request = request
        self.pn = pn  # Participant number, since we already may have it...


class SpeakerAddedEvent(SpeakerListUpdatedEvent):
    pass


class SpeakerRemovedEvent(SpeakerListUpdatedEvent):
    pass


class SpeakerFinishedEvent(SpeakerListUpdatedEvent):
    pass
