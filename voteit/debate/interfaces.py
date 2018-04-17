from pyramid.interfaces import IDict
from zope.interface import Attribute
from zope.interface import Interface


class ISpeakerLists(IDict):
    """ Multi-adapter that adapts a Meeting and a request.

        Implements a dict-like interface to handle speaker lists, with the exception that
        even empty objects are treated as True.

        You may register several of these to be able to change functionality.
        Make sure to set a different name.
    """
    name = Attribute("This is the same as the adapters name.")
    context = Attribute("Adapted meeting.")
    request = Attribute("Adapted request.")
    settings = Attribute("Configuration for this meeting.")

    #speaker_lists = Attribute("Storage for all speaker lists.")
    #active_list_name = Attribute("Get or set the name of the active list. Must be either None or a list that exists.")

    def get_list_names(uid):
        """ Return names (keys) of all lists that handle the context that this UID represents. """

    def get_lists_in(uid):
        """ Return all lists relevant to this UID. """

    def add_list_to(context):
        """ Add a list to this context, which must be an agenda item. """

    def add_to_list(pn, sl, override = False):
        """ Add participant number (pn) to the speaker list (sl) object.
            If override is true, add even if the list is closed.
        """

    def get_state_title(sl, translate = True):
        """ Return state title of sl."""

    def shuffle(sl):
        """ Shuffle speakers. The default implementation minds users current comparison value.
        """

    def get_position(pn, sl):
        """ Return the position this participant number would receive in this list
            if they were to add themselves. Override this method to change sorting functionality.
        """

    def get_list_number_for(pn, sl):
        """ The list this participant number would enter if added.
        """


class ISpeakerListSettings(IDict):
    pass


# class ISpeakerListPlugin(Interface):
#     """ pn is short for participant number. """
#     name = Attribute("The name of the wrapped list - not the name of the adapter!")
#     plugin_name = Attribute("Same as the adapters name")
#     plugin_title = Attribute("Title used when selecting this plugin.")
#     plugin_description = Attribute("Description of the plugin.")
#     title = Attribute("Title of the wrapped object")
#     speakers = Attribute("Same as the wrapped object")
#     speaker_log = Attribute("Same as the wrapped speaker list")
#     current = Attribute("Same as the wrapped speaker list")
#     state = Attribute("Set and get the state for the wrapped speaker list")
#     settings = Attribute("Get all values that the current SpeakerListSettingsSchema stores on a meeting. "
#                          "It also injects default values for speaker_list_count and safe_positions if they aren't present.")
#
#     def add(pn, override = False):
#         """ Add pn to list. It won't fail if pn is already in the list or if the list is closed.
#
#             override
#                 Bool - if true, pn will be added to speakers even if the list is closed. (Useful for moderators)
#         """
#
#     def get_position(pn):
#         """ Get the position for pn if pn would enter the list. """
#
#     def get_stats(pn, format = True):
#         """ Returns a tuple consisting of number of spoken times and total number of seconds spoken for 'pn'.
#             If format is True, return a string instead -> HH:MM:SS.
#         """
#
#     def shuffle():
#         """ Shuffle speakers in queue. Speaker lists are taken into consideration. """
#
#     def get_number_for(pn):
#         """ Get list number for 'pn'. Note that this is not number of times in the log, but
#             the speaker list number. A person who's spoken 5 times in a meeting with 2
#             speaker lists still has a number of 2.
#         """
#
#     def speaker_active(pn):
#         """ Set a speaker from speakers list as active.
#             Will also remove speaker from speakers list.
#         """
#
#     def speaker_finished(pn, seconds):
#         """ Set pn as finished. Both pn and seconds must be in int. """
#
#     def speaker_undo():
#         """ Undo starting the active speaker. The active speaker - if it exists - will
#             be placed first int the queue.
#         """
#
#     def get_state_title():
#         """ Return title of current speaker list state. """


class ISpeakerList(Interface):
    """ A persistent speaker list. Implements all list like things."""
    name = Attribute("Internal id of this speaker list.")
    speaker_log = Attribute("An IOBTree with speaker id as key and then a list with seonds this person has spoken.")
    current = Attribute("Current speaker id. Either None if no one is set, or an int.")
    title = Attribute("Readable title")
    state = Attribute("State, either open or closed")

    def start(pn):
        """ Start speaker, if it exist within this list.
            Returns same number if it was started.
        """

    def finish(pn):
        """ Finish speaker if it was active.
        """

    def undo():
        """ Undo starting current speaker.
            Returns its number if one was active.
        """
