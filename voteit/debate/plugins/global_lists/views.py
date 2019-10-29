from betahaus.viewcomponent import view_action

from voteit.debate.plugins.global_lists.models import GlobalLists
from voteit.debate.views import CONTEXTLIST_SLOT, USERDATA_SLOT


@view_action(USERDATA_SLOT, 'time_restriction')
def time_restriction(user, request, va, pn=None, sl=None, **kw):
    """ Add key 'time_restriction' to returned data.
    """
    if request.speaker_lists.name == GlobalLists.name:
        try:
            return request.speaker_lists.restrictions_active[sl.name][pn]
        except IndexError:
            pass


@view_action(CONTEXTLIST_SLOT, 'available_timeslots')
def available_timeslots(user, request, va, pn=None, sl=None, **kw):
    """ Add key 'available_timeslots' to returned data.
    """
    if pn is not None and request.speaker_lists.name == GlobalLists.name:
        return request.speaker_lists.available_restrictions
    return []


def includeme(config):
    config.scan(__name__)
