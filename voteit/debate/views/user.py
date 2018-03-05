from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem

from voteit.debate.views.base import BaseSLView
from voteit.debate.views.json import JSONView


@view_config(
    context=IAgendaItem,
    permission=security.VIEW,
    name='_user_list_act',
    renderer='json')
class ListActionsView(JSONView):

    def __call__(self):
        action_name = self.request.params.get('action')
        action = getattr(self, 'action_%s' % action_name, None)
        if not action:
            raise HTTPBadRequest('No such action')
        list_name = self.request.params.get('sl')
        try:
            sl = self.request.speaker_lists[list_name]
        except KeyError:
            raise HTTPBadRequest('No such list')
        pn = self.participant_numbers.userid_to_number.get(self.request.authenticated_userid, None)
        if pn is None:
            raise HTTPBadRequest("You don't have a participant number")
        return action(sl, pn)

    def action_add(self, sl, pn):
        if sl.open():
            self.request.speaker_lists.add_to_list(pn, sl)
        return self.context_list_stats_view()

    def action_remove(self, sl, pn):
        if pn in sl:
            sl.remove(pn)
        return self.context_list_stats_view()


def includeme(config):
    config.scan(__name__)
