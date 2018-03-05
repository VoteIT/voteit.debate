from six import StringIO
import csv
from datetime import timedelta
from decimal import Decimal

from arche.views.base import BaseView
from arche.views.base import DefaultEditForm
from betahaus.viewcomponent import view_action
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden, HTTPBadRequest, HTTPNotFound
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render
from pyramid.response import Response
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.traversal import find_interface
from pyramid.view import view_config
from pyramid.view import view_defaults
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.views.agenda_item import AgendaItemView
from voteit.core.views.control_panel import control_panel_category
from voteit.core.views.control_panel import control_panel_link
from voteit.debate.views.base import BaseSLView
from voteit.irl.models.interfaces import IParticipantNumbers
from zope.interface.interfaces import ComponentLookupError

from voteit.debate import _
from voteit.debate.interfaces import ISpeakerLists, ISpeakerListSettings


# @view_defaults(context=IMeeting,
#                name="speaker_list_action",
#                permission=security.MODERATE_MEETING,
#                renderer='json')
# class ListActions(BaseActionView):
#     def _tmp_redirect_url(self):
#         # FIXME: Remove this, all functions should load via js / json
#         url = self.request.resource_url(self.context, self.ai_name, 'manage_speaker_list')
#         return HTTPFound(location=url)
#
#     @view_config(request_param="action=add")
#     def add(self):
#         ai = self.get_ai()
#         if ai:
#             self.slists.add_contextual_list(ai)
#             self.success()
#         if not self.request.is_xhr:
#             return HTTPFound(location=self.request.resource_url(ai))
#         return self.response
#
#     @view_config(request_param="action=set_state")
#     def set_state(self):
#         # FIXME: proper js function
#         state = self.request.params.get('state')
#         if state:
#             self.action_list.state = state
#             self.success()
#         return self._tmp_redirect_url()
#
#     @view_config(request_param="action=delete")
#     def delete(self):
#         # FIXME: proper js function
#         if self.list_name in self.slists:
#             del self.slists[self.list_name]
#             self.success()
#         return self._tmp_redirect_url()
#
#     @view_config(request_param="action=rename")
#     def rename(self):
#         new_name = self.request.params.get('list_title_rename')
#         if new_name:
#             self.action_list.title = new_name
#             self.success()
#         return self.response
#
#     @view_config(request_param="action=active")
#     def active(self):
#         # FIXME: proper js function
#         if self.list_name in self.slists:
#             self.slists.active_list_name = self.list_name
#             self.success()
#         return self._tmp_redirect_url()
#
#     @view_config(request_param="action=undo")
#     def undo(self):
#         if self.action_list.speaker_undo() is not None:
#             self.success()
#         return self.response
#
#     @view_config(request_param="action=shuffle")
#     def shuffle(self):
#         self.action_list.shuffle()
#         self.success()
#         return self.response
#
#     @view_config(request_param="action=clear")
#     def clear(self):
#         self.action_list.speaker_log.clear()
#         self.success()
#         return self.response
#
#     @view_config(request_param="action=populate_from_proposals")
#     def populate_from_proposals(self):
#         result = populate_from_proposals(self.action_list)
#         msg = _("speakers_from_published_props",
#                 default=u"Added ${count} speakers from published proposals.",
#                 mapping={'count': result})
#         self.response['message'] = msg
#         self.success()
#         return self._tmp_redirect_url()



# @view_defaults(context=IMeeting, name="speaker_action", permission=security.MODERATE_MEETING,
#                renderer="json")
# class SpeakerActions(BaseActionView):
#     def _get_pn(self):
#         pn = self.request.params.get('pn', None)
#         if pn:
#             return int(pn)
#
#     @view_config(request_param="action=add")
#     def add(self):
#         pn = self.request.POST.get('pn', '')
#         if not pn:
#             return self.response
#         try:
#             pn = int(pn)
#         except ValueError:
#             self.response['message'] = self.request.localizer.translate(
#                 _('${num} is not a valid number', mapping={'num': pn})
#             )
#             return self.response
#         if pn in self.action_list.speakers:
#             # Shouldn't happen since js handles this
#             self.response['message'] = _("Already in list")
#             return self.response
#         self.action_list.add(pn, override=True)
#         self.success()
#         return self.response
#
#     @view_config(request_param="action=active")
#     def active(self):
#         pn = self._get_pn()
#         if pn is None and len(self.action_list.speakers) > 0:
#             pn = self.action_list.speakers[0]
#         if pn is not None and self.action_list.speaker_active(pn) is not None:
#             self.success()
#             userid = self.participant_numbers.number_to_userid.get(pn)
#             self.response['active_speaker'] = speaker_item_moderator(pn, self, self.action_list,
#                                                                      userid=userid)
#         return self.response
#
#     @view_config(request_param="action=remove")
#     def remove(self):
#         pn = self._get_pn()
#         if pn in self.action_list.speakers:
#             self.action_list.speakers.remove(pn)
#             self.success()
#         return self.response
#
#     @view_config(request_param="action=finished")
#     def finished(self):
#         pn = self.action_list.current
#         seconds = int(self.request.params['seconds'])
#         if self.action_list.speaker_finished(pn, seconds) is not None:
#             self.success()
#         return self.response


# @view_defaults(context=IMeeting,
#                permission=security.MODERATE_MEETING)
# class ManageSpeakerList(AgendaItemView):
#
#     @reify
#     def slists(self):
#         return ISpeakerLists(self.context)
#
#     @reify
#     def participant_numbers(self):
#         return IParticipantNumbers(self.context)
#
#     @reify
#     def active_list(self):
#         return self.slists.get(self.slists.active_list_name)
#
#     @view_config(name="manage_speaker_list",
#                  permission=security.MODERATE_MEETING,
#                  context=IAgendaItem,
#                  renderer="voteit.debate:templates/manage_speaker_list.pt")
#     def manage_speaker_list_view(self):
#         voteit_debate_manage_speakers_js.need()
#         voteit_debate_speaker_view_styles.need()
#         response = {}
#         response[
#             'context_active'] = self.slists.active_list_name in self.slists.get_contexual_list_names(
#             self.context)
#         response['active_list'] = self.slists.get(self.slists.active_list_name)
#         response['speaker_item'] = self.speaker_item
#         response['speaker_list_controls'] = speaker_list_controls_moderator(self, self.slists,
#                                                                             self.context)
#         return response
#
#     @view_config(name="_speaker_queue_moderator",
#                  permission=security.MODERATE_MEETING,
#                  renderer="voteit.debate:templates/speaker_queue_moderator.pt")
#     def speaker_queue_moderator(self):
#         response = {}
#         response['active_list'] = self.active_list
#         response['speaker_item'] = self.speaker_item
#         response['use_lists'] = self.request.meeting.get_field_value('speaker_list_count', 1)
#         response['safe_pos'] = self.request.meeting.get_field_value('safe_positions', 0)
#         return response
#
#     @view_config(name="_speaker_log_moderator",
#                  permission=security.MODERATE_MEETING,
#                  renderer="voteit.debate:templates/speaker_log_moderator.pt")
#     def speaker_log_moderator(self):
#         response = {}
#         response['active_list'] = self.active_list
#         number_to_profile_tag = {}
#         for pn in self.active_list.speaker_log.keys():
#             if pn in self.participant_numbers.number_to_userid:
#                 userid = self.participant_numbers.number_to_userid[pn]
#                 number_to_profile_tag[pn] = self.request.creators_info([userid], portrait=False)
#             else:
#                 number_to_profile_tag[pn] = '-'
#         response['number_to_profile_tag'] = number_to_profile_tag
#         response['format_secs'] = self.format_seconds
#         return response
#
#     @view_config(name="_speaker_lists_moderator", context=IAgendaItem,
#                  permission=security.MODERATE_MEETING)
#     def speaker_lists(self):
#         if self.request.is_xhr:
#             return Response(speaker_list_controls_moderator(self, self.slists, self.context))
#         # Fallback in case of js error
#         return HTTPFound(location=self.request.resource_url(self.context, 'manage_speaker_list'))
#
#     def speaker_item(self, pn):
#         userid = self.participant_numbers.number_to_userid.get(int(pn))
#         return speaker_item_moderator(pn, self, self.active_list, userid=userid)
#
#     def format_seconds(self, secs):
#         val = str(timedelta(seconds=int(secs)))
#         try:
#             return ":".join([x for x in val.split(':') if int(x)])
#         except ValueError:
#             return val


@view_defaults(
    context=IAgendaItem,
    permission=security.MODERATE_MEETING,)
class ManageListsView(BaseSLView):
    list_controls_tpl = 'voteit.debate:templates/manage_list_controls.pt'

    @view_config(
        name='manage_speaker_lists',
        renderer='voteit.debate:templates/manage_speaker_lists.pt')
    def main(self):
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
        return {'list_controls': list_controls, 'context_active': True, 'edit_log_item_url': edit_log_item_url}

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

    @view_config(name='_activate_slist')
    def activate_slist(self):
        name = "/".join(self.request.subpath)
        if name in self.request.speaker_lists:
            self.request.speaker_lists.set_active_list(name)
            return HTTPFound(location=self.request.resource_url(self.context, 'manage_speaker_lists'))
        raise HTTPNotFound('No such list')


@view_config(
    context=IAgendaItem,
    permission=security.MODERATE_MEETING,
    name='_list_act',
    renderer='json')
class ListActionsView(BaseSLView):

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
        return action(sl)

    def _get_pn(self):
        pn = self.request.params.get('pn', None)
        try:
            return int(pn)
        except (ValueError, TypeError):
            raise HTTPBadRequest('Bad participant number value')

    def action_add(self, sl):
        pn = self._get_pn()
        self.request.speaker_lists.add_to_list(pn, sl, override=True)
        return self.get_queue_response(sl)

    def action_start(self, sl):
        pn = self._get_pn()
        if sl.current != None:
            raise HTTPBadRequest("Another speaker is already active")
        sl.start(pn)
        return self.get_queue_response(sl)

    def action_finish(self, sl):
        pn = self._get_pn()
        sl.finish(pn)
        return self.get_queue_response(sl)

    def action_undo(self, sl):
        sl.undo()
        return self.get_queue_response(sl)

    def action_remove(self, sl):
        pn = self._get_pn()
        if pn in sl:
            sl.remove(pn)
        return self.get_queue_response(sl)

    def action_shuffle(self, sl):
        self.request.speaker_lists.shuffle(sl)
        return self.get_queue_response(sl)


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
