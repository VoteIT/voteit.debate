from zope.interface import Attribute
from zope.interface import Interface


class ISpeakerListHandler(Interface):
    """ Adapts an Agenda Item and handles speaker lists locally. """


class ISpeakerList(Interface):
    """ A persistent speaker list. """
    speakers = Attribute("A persistent list of speakers userids. Must be in correct order.")
    speaker_log = Attribute("An OOBTree with speaker id as key and then a list with seonds this person has spoken.")

    def add(userid):
        """ Add userid to speakers """

    def remove(index):
        """ Remove at this position. Users can be added several times to the list.
        """

    def set(value):
        """ Set the list to these values. Must be possible to convert to a persistent list.
        """

    def speaker_finished(seconds):
        """ The top speaker on the list has now finished. Move item to log, and log number of seconds.
        """
