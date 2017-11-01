import StringIO
import csv
from datetime import timedelta
from decimal import Decimal

from arche.views.base import BaseView
from arche.views.base import DefaultEditForm
from betahaus.viewcomponent import view_action
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
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
from voteit.irl.models.interfaces import IParticipantNumbers

from voteit.debate import _
from voteit.debate.fanstaticlib import voteit_debate_fullscreen_speakers_css
from voteit.debate.fanstaticlib import voteit_debate_fullscreen_speakers_js
from voteit.debate.fanstaticlib import voteit_debate_manage_speakers_js
from voteit.debate.fanstaticlib import voteit_debate_speaker_view_styles
from voteit.debate.interfaces import ISpeakerLists
from voteit.debate.models import populate_from_proposals


class BaseActionView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.list_name = self.request.params.get('list_name', None)
        self.ai_name = self.request.params.get('ai_name', None)
        self.response = {'action': self.request.params.get('action', None),
                         'list_name': self.list_name,
                         'ai_name': self.ai_name,
                         'success': False}

    @reify
    def slists(self):
        return self.request.registry.getAdapter(self.context, ISpeakerLists)

    @reify
    def action_list(self):
        return self.slists.get(self.list_name)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.context, IParticipantNumbers)

    def success(self):
        self.response['success'] = True

    def get_ai(self):
        if self.ai_name in self.context:
            ai = self.context[self.ai_name]
            if IAgendaItem.providedBy(ai):
                return ai


@view_defaults(context=IMeeting,
               name="speaker_list_action",
               permission=security.MODERATE_MEETING,
               renderer='json')
class ListActions(BaseActionView):
    def _tmp_redirect_url(self):
        # FIXME: Remove this, all functions should load via js / json
        url = self.request.resource_url(self.context, self.ai_name, 'manage_speaker_list')
        return HTTPFound(location=url)

    @view_config(request_param="action=add")
    def add(self):
        ai = self.get_ai()
        if ai:
            self.slists.add_contextual_list(ai)
            self.success()
        if not self.request.is_xhr:
            return HTTPFound(location=self.request.resource_url(ai))
        return self.response

    @view_config(request_param="action=set_state")
    def set_state(self):
        # FIXME: proper js function
        state = self.request.params.get('state')
        if state:
            self.action_list.state = state
            self.success()
        return self._tmp_redirect_url()

    @view_config(request_param="action=delete")
    def delete(self):
        # FIXME: proper js function
        if self.list_name in self.slists:
            del self.slists[self.list_name]
            self.success()
        return self._tmp_redirect_url()

    @view_config(request_param="action=rename")
    def rename(self):
        new_name = self.request.params.get('list_title_rename')
        if new_name:
            self.action_list.title = new_name
            self.success()
        return self.response

    @view_config(request_param="action=active")
    def active(self):
        # FIXME: proper js function
        if self.list_name in self.slists:
            self.slists.active_list_name = self.list_name
            self.success()
        return self._tmp_redirect_url()

    @view_config(request_param="action=undo")
    def undo(self):
        if self.action_list.speaker_undo() is not None:
            self.success()
        return self.response

    @view_config(request_param="action=shuffle")
    def shuffle(self):
        self.action_list.shuffle()
        self.success()
        return self.response

    @view_config(request_param="action=clear")
    def clear(self):
        self.action_list.speaker_log.clear()
        self.success()
        return self.response

    @view_config(request_param="action=populate_from_proposals")
    def populate_from_proposals(self):
        result = populate_from_proposals(self.action_list)
        msg = _("speakers_from_published_props",
                default=u"Added ${count} speakers from published proposals.",
                mapping={'count': result})
        self.response['message'] = msg
        self.success()
        return self._tmp_redirect_url()


@view_defaults(context=IMeeting, name="speaker_action", permission=security.MODERATE_MEETING,
               renderer="json")
class SpeakerActions(BaseActionView):
    def _get_pn(self):
        pn = self.request.params.get('pn', None)
        if pn:
            return int(pn)

    @view_config(request_param="action=add")
    def add(self):
        pn = self.request.POST.get('pn', '')
        if not pn:
            return self.response
        try:
            pn = int(pn)
        except ValueError:
            self.response['message'] = self.request.localizer.translate(
                _('${num} is not a valid number', mapping={'num': pn})
            )
            return self.response
        if pn in self.action_list.speakers:
            # Shouldn't happen since js handles this
            self.response['message'] = _("Already in list")
            return self.response
        self.action_list.add(pn, override=True)
        self.success()
        return self.response

    @view_config(request_param="action=active")
    def active(self):
        pn = self._get_pn()
        if pn is None and len(self.action_list.speakers) > 0:
            pn = self.action_list.speakers[0]
        if pn is not None and self.action_list.speaker_active(pn) is not None:
            self.success()
            userid = self.participant_numbers.number_to_userid.get(pn)
            self.response['active_speaker'] = speaker_item_moderator(pn, self, self.action_list,
                                                                     userid=userid)
        return self.response

    @view_config(request_param="action=remove")
    def remove(self):
        pn = self._get_pn()
        if pn in self.action_list.speakers:
            self.action_list.speakers.remove(pn)
            self.success()
        return self.response

    @view_config(request_param="action=finished")
    def finished(self):
        pn = self.action_list.current
        seconds = int(self.request.params['seconds'])
        if self.action_list.speaker_finished(pn, seconds) is not None:
            self.success()
        return self.response


def speaker_item_moderator(pn, view, slist, userid=None):
    use_lists = slist.settings['speaker_list_count']
    safe_positions = slist.settings['safe_positions']
    response = {}
    if userid:
        response['user_info'] = view.request.creators_info([userid], portrait=False)
    else:
        response['user_info'] = _(u"(No user associated)")
    response['slist'] = slist
    response['pn'] = pn
    response['is_active'] = pn == slist.current
    response['is_locked'] = pn in slist.speakers and slist.speakers.index(pn) < safe_positions
    return render("voteit.debate:templates/speaker_item.pt", response, request=view.request)


def speaker_list_controls_moderator(view, slists, ai):
    assert IAgendaItem.providedBy(ai)
    response = {}
    response['context'] = ai
    response['active_list'] = slists.get(slists.active_list_name)
    response['context_lists'] = slists.get_contextual_lists(ai)
    return render("templates/speaker_list_controls_moderator.pt", response, request=view.request)


@view_defaults(context=IMeeting,
               permission=security.MODERATE_MEETING)
class ManageSpeakerList(AgendaItemView):
    @reify
    def slists(self):
        return self.request.registry.getAdapter(self.request.meeting, ISpeakerLists)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.request.meeting, IParticipantNumbers)

    @reify
    def active_list(self):
        return self.slists.get(self.slists.active_list_name)

    @view_config(name="manage_speaker_list",
                 permission=security.MODERATE_MEETING,
                 context=IAgendaItem,
                 renderer="voteit.debate:templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        voteit_debate_speaker_view_styles.need()
        response = {}
        response[
            'context_active'] = self.slists.active_list_name in self.slists.get_contexual_list_names(
            self.context)
        response['active_list'] = self.slists.get(self.slists.active_list_name)
        response['speaker_item'] = self.speaker_item
        response['speaker_list_controls'] = speaker_list_controls_moderator(self, self.slists,
                                                                            self.context)
        return response

    @view_config(name="_speaker_queue_moderator",
                 permission=security.MODERATE_MEETING,
                 renderer="voteit.debate:templates/speaker_queue_moderator.pt")
    def speaker_queue_moderator(self):
        response = {}
        response['active_list'] = self.active_list
        response['speaker_item'] = self.speaker_item
        response['use_lists'] = self.request.meeting.get_field_value('speaker_list_count', 1)
        response['safe_pos'] = self.request.meeting.get_field_value('safe_positions', 0)
        return response

    @view_config(name="_speaker_log_moderator",
                 permission=security.MODERATE_MEETING,
                 renderer="voteit.debate:templates/speaker_log_moderator.pt")
    def speaker_log_moderator(self):
        response = {}
        response['active_list'] = self.active_list
        number_to_profile_tag = {}
        for pn in self.active_list.speaker_log.keys():
            if pn in self.participant_numbers.number_to_userid:
                userid = self.participant_numbers.number_to_userid[pn]
                number_to_profile_tag[pn] = self.request.creators_info([userid], portrait=False)
            else:
                number_to_profile_tag[pn] = '-'
        response['number_to_profile_tag'] = number_to_profile_tag
        response['format_secs'] = self.format_seconds
        return response

    @view_config(name="_speaker_lists_moderator", context=IAgendaItem,
                 permission=security.MODERATE_MEETING)
    def speaker_lists(self):
        if self.request.is_xhr:
            return Response(speaker_list_controls_moderator(self, self.slists, self.context))
        # Fallback in case of js error
        return HTTPFound(location=self.request.resource_url(self.context, 'manage_speaker_list'))

    def speaker_item(self, pn):
        userid = self.participant_numbers.number_to_userid.get(int(pn))
        return speaker_item_moderator(pn, self, self.active_list, userid=userid)

    def format_seconds(self, secs):
        val = str(timedelta(seconds=int(secs)))
        try:
            return ":".join([x for x in val.split(':') if int(x)])
        except ValueError:
            return val


@view_config(name="edit_speaker_log",
             context=IMeeting,
             permission=security.MODERATE_MEETING,
             renderer="arche:templates/form.pt")
class EditSpeakerLogForm(DefaultEditForm):
    """ Edit log entries for a specific speaker. """
    type_name = 'SpeakerLists'
    schema_name = 'edit_speaker_log'
    title = _("Edit speaker log")

    @reify
    def edit_list(self):
        slists = self.request.registry.getAdapter(self.request.meeting, ISpeakerLists)
        speaker_list_name = self.request.GET['speaker_list']
        return slists.speaker_lists[speaker_list_name]

    @reify
    def users_speaker_log(self):
        speaker = int(self.request.GET['speaker'])
        return self.edit_list.speaker_log[speaker]

    def appstruct(self):
        return {'logs': self.users_speaker_log}

    def save_success(self, appstruct):
        del self.users_speaker_log[:]
        self.users_speaker_log.extend(appstruct['logs'])
        self.flash_messages.add(self.default_success)
        return self._redirect()

    def _redirect(self):
        ai = find_interface(self.edit_list, IAgendaItem)
        url = self.request.resource_url(ai, 'manage_speaker_list')
        return HTTPFound(location=url)

    def cancel_success(self, *args):
        return self._redirect()


@view_config(context=IMeeting,
             name="speaker_list_settings",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class SpeakerListSettingsForm(DefaultEditForm):
    schema_name = 'settings'
    type_name = 'SpeakerLists'
    title = _("Speaker list settings")

    def appstruct(self):
        return self.context.get_field_appstruct(self.schema)

    def save_success(self, appstruct):
        self.context.set_field_appstruct(appstruct)
        self.flash_messages.add(self.default_success, type="success")
        return HTTPFound(location=self.request.resource_url(self.context))


@view_defaults(context=IMeeting)
class FullscreenSpeakerList(BaseView):
    @view_config(name="fullscreen_speaker_list",
                 permission=NO_PERMISSION_REQUIRED,
                 renderer="voteit.debate:templates/fullscreen_view.pt")
    def fullscreen_view(self):
        voteit_debate_fullscreen_speakers_js.need()
        voteit_debate_fullscreen_speakers_css.need()
        return {}

    @view_config(name="_fullscreen_list",
                 permission=NO_PERMISSION_REQUIRED,
                 renderer="voteit.debate:templates/fullscreen_list.pt")
    def fullscreen_list(self):
        slists = self.request.registry.getAdapter(self.context, ISpeakerLists)
        active_list = slists.get(slists.active_list_name)
        participant_numbers = self.request.registry.getAdapter(self.context, IParticipantNumbers)
        root = self.context.__parent__
        speaker_profiles = {}
        if active_list:
            if active_list.current != None:  # Note could be int 0!
                userid = participant_numbers.number_to_userid.get(active_list.current, None)
                if userid:
                    speaker_profiles[active_list.current] = root.users[userid]
            for num in active_list.speakers:
                userid = participant_numbers.number_to_userid.get(num)
                if userid:
                    speaker_profiles[num] = root.users[userid]
        return dict(active_list=active_list, speaker_profiles=speaker_profiles)


class UserSpeakerLists(BaseView):
    @reify
    def slists(self):
        return self.request.registry.getAdapter(self.request.meeting, ISpeakerLists)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.request.meeting, IParticipantNumbers)

    @view_config(name="_user_speaker_lists",
                 context=IAgendaItem,
                 permission=security.VIEW,
                 renderer="voteit.debate:templates/user_speaker.pt")
    def view(self):
        action = self.request.GET.get('action', None)
        pn = self.participant_numbers.userid_to_number.get(self.request.authenticated_userid, None)
        use_lists = self.request.meeting.get_field_value('speaker_list_count', 1)
        safe_pos = self.request.meeting.get_field_value('safe_positions', 0)
        max_times_in_list = self.request.meeting.get_field_value('max_times_in_list', 0)

        def _over_limit(sl, pn):
            return max_times_in_list and len(sl.speaker_log.get(pn, ())) >= max_times_in_list

        if pn != None and action:
            list_name = self.request.GET.get('list_name', None)
            if list_name not in self.slists.speaker_lists:
                raise HTTPForbidden(_(u"Speaker list doesn't exist"))
            sl = self.slists[list_name]
            if action == u'add' and not _over_limit(sl, pn):
                sl.add(pn)
            if action == u'remove':
                if pn in sl.speakers:
                    sl.speakers.remove(pn)
        response = {}
        response['speaker_lists'] = self.slists.get_contextual_lists(self.context)
        response['active_list'] = self.slists.get(self.slists.active_list_name)
        response['pn'] = pn
        response['use_lists'] = use_lists
        response['safe_pos'] = safe_pos
        response['over_limit'] = _over_limit
        response['max_times_in_list'] = max_times_in_list
        if pn != None:
            def _show_add(sl, pn):
                return pn != None and sl.state == 'open' and pn not in sl.speakers

            response['show_add'] = _show_add
        return response

    @view_config(name="speaker_statistics", context=IMeeting, permission=security.VIEW,
                 renderer="voteit.debate:templates/speaker_statistics.pt")
    def speaker_statistics_view(self):
        response = {}
        response['number_to_userid'] = self.participant_numbers.number_to_userid
        results = {}
        maxval = 0
        for sl in self.slists.speaker_lists.values():
            for (pn, entries) in sl.speaker_log.items():
                current = results.setdefault(pn, [])
                current.extend(entries)
                this_val = sum(current)
                if this_val > maxval:
                    maxval = this_val
        response['results'] = [(x, results[x]) for x in sorted(results)]

        def _get_percentage(num):
            try:
                return int(round(Decimal(num) / maxval * 100))
            except:
                return u"0%"

        response['get_perc'] = _get_percentage
        return response

    @view_config(name='speaker_statistics.csv', context=IMeeting, permission=security.VIEW)
    def export(self):
        output = StringIO.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([self.context.title.encode('utf-8')])
        writer.writerow([self.request.localizer.translate(_(u"Speaker statistics"))])
        writer.writerow(["#", self.request.localizer.translate(_(u"Seconds"))])
        for sl in self.slists.speaker_lists.values():
            if not len(sl.speaker_log):
                continue
            writer.writerow([""])
            writer.writerow([sl.title.encode('utf-8')])
            for (pn, entries) in sl.speaker_log.items():
                for entry in entries:
                    writer.writerow([pn, entry])
        contents = output.getvalue()
        output.close()
        return Response(content_type='text/csv', body=contents)


def _debate_is_active(context, request, va):
    return context.enable_voteit_debate


@view_action('agenda_actions', 'manage_speaker_lists',
             title=_("Speakers"),
             interface=IAgendaItem)
def _manage_speaker_list(context, request, va, **kw):
    if request.is_moderator and request.meeting.enable_voteit_debate:
        return """<li class="%s"><a href="%s">%s</a></li>""" % (
            request.view_name == 'manage_speaker_list' and 'active' or None,
            request.resource_url(context, 'manage_speaker_list'),
            request.localizer.translate(va.title),
        )


def includeme(config):
    config.scan(__name__)
    config.add_view_action(
        control_panel_category,
        'control_panel', 'debate',
        title=_("Speaker lists"),
        panel_group='debate_control_panel',
        check_active=_debate_is_active
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'settings',
        title=_("Settings"),
        permission=security.MODERATE_MEETING,
        view_name='speaker_list_settings'
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'speaker_statistics',
        title=_("Statistics"),
        view_name='speaker_statistics'
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'fullscreen_speaker_list',
        title=_("Fullscreen"),
        view_name='fullscreen_speaker_list'
    )
