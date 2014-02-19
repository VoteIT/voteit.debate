from zope.interface import Attribute
from zope.interface import Interface


class ISpeakerLists(Interface):
    """ Adapts a Meeting object and handles speaker lists locally.
        Implements a dict-like interface to handle speaker lists, with the exception that
        even empty objects are treated as True.
        
        Whenever a speaker list is fetched, it will be wrapped in the selected
        ISpeakerListPlugin adapter by default. The adapter implements all functionality
        needed to interact with each speaker list.
    """
    speaker_list_plugin = Attribute("Name of the plugin to wrap speaker list objects in. This is the same as the adapter name.")
    speaker_lists = Attribute("Storage for all speaker lists.")
    active_list_name = Attribute("Get or set the name of the active list. Must be either None or a list that exists.")

    def add(key, value, parent = None):
        """ Add speaker list (value). It will also add an AgendaItem as parent, which
            can either be specified through the parent-kw or looked up from the request.context attribute.
        """

    def get(key, default = None):
        """ Return a speaker list wrapped in correct ISpeakerListPlugin adapter. """

    def get_contexual_list_names(context):
        """ Return names (keys) of all lists that handle this context. """

    def get_contextual_lists(context):
        """ Get all contextual lists objects (wrapped) for this context. """

    def add_contextual_list(context):
        """ Add a list to this context, which must be an agenda item. """


class ISpeakerListPlugin(Interface):
    """ pn is short for participant number. """
    name = Attribute("The name of the wrapped list - not the name of the adapter!")
    plugin_name = Attribute("Same as the adapters name")
    plugin_title = Attribute("Title used when selecting this plugin.")
    plugin_description = Attribute("Description of the plugin.")
    title = Attribute("Title of the wrapped object")
    speakers = Attribute("Same as the wrapped object")
    speaker_log = Attribute("Same as the wrapped speaker list")
    current = Attribute("Same as the wrapped speaker list")
    state = Attribute("Set and get the state for the wrapped speaker list")
    settings = Attribute("Get all values that the current SpeakerListSettingsSchema stores on a meeting. "
                         "It also injects default values for speaker_list_count and safe_positions if they aren't present.")

    def add(pn, override = False):
        """ Add pn to list. It won't fail if pn is already in the list or if the list is closed.
        
            override
                Bool - if true, pn will be added to speakers even if the list is closed. (Useful for moderators)
        """

    def get_position(pn):
        """ Get the position for pn if pn would enter the list. """

    def get_stats(pn, format = True):
        """ Returns a tuple consisting of number of spoken times and total number of seconds spoken for 'pn'.
            If format is True, return a string instead -> HH:MM:SS.
        """

    def shuffle():
        """ Shuffle speakers in queue. Speaker lists are taken into consideration. """
        #FIXME: Should safe positions matter too?

    def get_number_for(pn):
        """ Get list number for 'pn'. Note that this is not number of times in the log, but
            the speaker list number. A person who's spoken 5 times in a meeting with 2
            speaker lists still has a number of 2.
        """

    def speaker_active(pn):
        """ Set a speaker from speakers list as active.
            Will also remove speaker from speakers list.
        """

    def speaker_finished(pn, seconds):
        """ Set pn as finished. Both pn and seconds must be in int. """

    def speaker_undo():
        """ Undo starting the active speaker. The active speaker - if it exists - will
            be placed first int the queue.
        """

    def get_state_title():
        """ Return title of current speaker list state. """


class ISpeakerList(Interface):
    """ A persistent speaker list. """
    name = Attribute("Internal id of this speaker list.")
    speakers = Attribute("A persistent list of speakers userids. Must be in correct order.")
    speaker_log = Attribute("An IOBTree with speaker id as key and then a list with seonds this person has spoken.")
    current = Attribute("Current speaker id. Either None if no one is set, or an int.")
    title = Attribute("Readable title")
    state = Attribute("State, either open or closed")
