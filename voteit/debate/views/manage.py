from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.view import view_defaults
from repoze.catalog.query import Eq
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.views.agenda_item import AgendaItemView

from voteit.debate import _
from voteit.debate.fanstaticlib import manage_static
from voteit.debate.interfaces import ISpeakerListSettings
from voteit.debate.views.base import BaseSLView


class ManageQueueView(BaseSLView):

    @view_config(context=IAgendaItem, name='_manage_speaker_item', permission=security.MODERATE_MEETING)
    def queue_view(self, sl=None):
        if sl is None:
            sl = self.sl
        user_pns = list(sl)
        if sl.current:
           user_pns.insert(0, sl.current)
        pn2u = self.participant_numbers.number_to_userid
        pn2user = {}
        for pn in user_pns:
            userid = pn2u.get(pn, None)
            if userid:
                user = self.request.root['users'].get(userid, None)
                if user:
                    pn2user[pn] = user
        response = dict(
            safe_count=self.request.speaker_lists.settings.get('safe_positions', 1),
            default_img=self.request.static_url('voteit.debate:static/default_user.png'),
            sl=sl,
            user_pns=user_pns,
            pn2user=pn2user,
        )
        tpl = self.request.speaker_lists.tpl_manage_speaker_item
        return render(tpl, response, request=self.request)


@view_defaults(
    context=IAgendaItem,
    permission=security.MODERATE_MEETING,)
class ManageListsView(ManageQueueView, AgendaItemView):
    list_controls_tpl = 'voteit.debate:templates/manage_list_controls.pt'

    @view_config(
        name='manage_speaker_lists',
        renderer='voteit.debate:templates/manage_speaker_lists.pt')
    def main(self):
        manage_static.need()
        list_controls = render(
            self.list_controls_tpl,
            self.list_controls(),
            request=self.request
        )
        edit_log_item_url = self.request.resource_url(
            self.request.meeting, 'edit_speaker_log',
            query = {
                'speaker_list': self.request.speaker_lists.get_active_list(),
            }
        )
        response = {'list_controls': list_controls, 'edit_log_item_url': edit_log_item_url}
        if self.context_active:
            sl = self.request.speaker_lists[self.active_name]
            response['rendered_queue'] = self.queue_view(sl=sl)
        return response

    @view_config(
        name='_manage_list_controls',
        renderer=list_controls_tpl)
    def list_controls(self):
        return {
            'context': self.context,
            'view': self,
            'context_lists': self.request.speaker_lists.get_lists_in(self.context.uid)
        }

    @view_config(name='_add_slist', renderer='json')
    def add(self):
        self.request.speaker_lists.add_list_to(self.context)
        if self.request.is_xhr:
            return {}
        return HTTPFound(location=self.request.resource_url(self.context, 'manage_speaker_lists'))

    @view_config(name='_m_act')
    def manage_action(self):
        """ Common actions, followed as links.
            Required params:
            sl (list name)
            action (what to do)
        """
        action_name = self.request.params.get('action')
        action = getattr(self, 'action_%s' % action_name, None)
        if not action:
            raise HTTPBadRequest('No such action')
        list_name = self.request.params.get('sl')
        try:
            sl = self.request.speaker_lists[list_name]
        except KeyError:
            raise HTTPBadRequest('No such list')
        action(sl)
        return HTTPFound(location=self.request.resource_url(self.context, 'manage_speaker_lists'))

    def action_activate(self, sl):
        self.request.speaker_lists.set_active_list(sl.name)

    def action_delete(self, sl):
        if sl.name in self.request.speaker_lists:
            del self.request.speaker_lists[sl.name]

    def action_state(self, sl):
        state = self.request.params.get('state', None)
        if state in self.request.speaker_lists.state_titles:
            sl.state = state

    def action_rename(self, sl):
        title = self.request.params.get('list_title_rename', None)
        if title:
            sl.title = title

    def action_populate(self, sl):
        handled_userids = set()
        found = 0
        query = Eq('workflow_state', 'published') & \
                Eq('type_name', 'Proposal')  & \
                Eq('path', resource_path(self.context))
        docids = self.request.root.catalog.query(query, sort_index = 'created')[1]
        for proposal in self.request.resolve_docids(docids, perm=None):
            if proposal.creator:
                handled_userids.add(proposal.creator[0])
        for userid in handled_userids:
            pn = self.participant_numbers.userid_to_number.get(userid, None)
            if pn and pn not in sl:
                self.request.speaker_lists.add_to_list(pn, sl, override=True)
                found += 1
        if found:
            self.flash_messages.add(_("Added ${num} speakers from proposals",
                                      mapping={'num': found}))
        else:
            self.flash_messages.add(_("No speakers found"))


@view_config(
    context=IAgendaItem,
    permission=security.MODERATE_MEETING,
    name='_list_act')
class ListActionsView(ManageQueueView):

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
        action(sl)
        if self.use_websockets:
            return Response(render('json', {'sockets': True}), request=self.request)
        else:
            return Response(self.queue_view(sl))

    def _get_pn(self):
        pn = self.request.params.get('pn', None)
        try:
            return int(pn)
        except (ValueError, TypeError):
            raise HTTPBadRequest('Bad participant number value')

    def action_add(self, sl):
        pn = self._get_pn()
        if pn not in self.participant_numbers:
            raise HTTPBadRequest('Bad participant number value')
        self.request.speaker_lists.add_to_list(pn, sl, override=True)

    def action_start(self, sl):
        pn = self._get_pn()
        if sl.current != None:
            raise HTTPBadRequest("Another speaker is already active")
        sl.start(pn)

    def action_finish(self, sl):
        if sl.current:
            sl.finish(sl.current)

    def action_undo(self, sl):
        sl.undo()

    def action_remove(self, sl):
        pn = self._get_pn()
        self.request.speaker_lists.remove_from_list(pn, sl)

    def action_shuffle(self, sl):
        self.request.speaker_lists.shuffle(sl)

    def action_refresh(self, sl):
        # We don't want a response here, see code above :)
        pass


def _manage_speaker_list(context, request, va, **kw):
    if request.is_moderator and \
            ISpeakerListSettings(request.meeting, {}).get('enable_voteit_debate', False):
        return """<li class="%s"><a href="%s">%s</a></li>""" % (
            request.view_name == 'manage_speaker_lists' and 'active' or None,
            request.resource_url(context, 'manage_speaker_lists'),
            request.localizer.translate(va.title),
        )


def includeme(config):
    config.scan(__name__)
    config.add_view_action(
        _manage_speaker_list,
        'agenda_actions', 'manage_speaker_lists',
        title=_("Speakers"),
        interface=IAgendaItem
    )
