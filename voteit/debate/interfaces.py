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


class ISpeakerListCategories(IDict):
    pass


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


class ISLCategory(Interface):
    pass
