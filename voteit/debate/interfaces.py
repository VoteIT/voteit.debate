from zope.interface import Attribute
from zope.interface import Interface


class ISpeakerListHandler(Interface):
    """ Adapts a Meeting object and handles speaker lists locally.
    """
    speaker_lists = Attribute("Storage for all speaker lists.")
    speaker_list_name = Attribute("Internal name (id) of the active speaker list. Not ment to be displayed.")

    def set_active_list(name):
        """ Set the name of the currently active list. Can also be None to unset. """

    def get_active_list():
        """ Return the currently active list, or None. """

    def get_contexual_list_names(context):
        """ Return all speaker list names for a specific context - sorted. """

    def get_contextual_lists(context):
        """ Return all speaker lists for a specific context - sorted. """

    def add_contextual_list(context):
        """ Create a new speaker list in this context.
            (Any context inside a meeting will do, but normally Agenda items are used.)
        """

    def remove_list(name):
        """ Remove a speaker list, and unset it as active if it was.
        """

    def get_expected_context_for(name):
        """ Return the agenda item this list is expected to belong to. This is a computationally expensive thing. """


class ISpeakerList(Interface):
    """ A persistent speaker list. """
    speakers = Attribute("A persistent list of speakers userids. Must be in correct order.")
    speaker_log = Attribute("An IOBTree with speaker id as key and then a list with seonds this person has spoken.")
    current = Attribute("Current speaker id. Either None if no one is set, or an int.")

    def get_expected_pos(name, use_lists = 1, safe_pos = 0):
        """ Get the expected entry position for name. (Where name is participant number, an int)
        """

    def get_stats(name, format = True):
        """ Returns a tuple consisting of number of spoken times and total number of seconds spoken for 'name'.
            If format is True, return a string instead -> HH:MM:SS.
        """

    def add(name, use_lists = 1, safe_pos = 0, override = False):
        """ Add name to speakers. Name is the delegate number. (An int)
            use_lists is a setting to promote speakers that have spoken less than others,
            also known as secondary speaker lists.
            safe_pos never promotes someone above this position. (To avoid shuffling the top of the list)
            Override means add even if a list is closed.
        """

    def remove(name):
        """ Remove name from list.
        """

    def set(value):
        """ Set the list to these values. Must be possible to convert to a persistent list.
        """

    def speaker_active(name):
        """ Set a speaker from speakers list as active.
            Will also remove speaker from speakers list.
        """

    def speaker_finished(seconds):
        """ The speaker set as current has finished speaking. Move item to log, and log number of seconds.
        """

    def speaker_undo():
        """ The ongoing speaker is removed and placed first in line. No time saved.
        """

    def set_state(state):
        """ Set a state, either open or closed.
        """

    def get_state_title():
        """ Get a translatable title for the current state.
        """

    def shuffle(use_lists = 1):
        """ Randomize order of the speakers. """
