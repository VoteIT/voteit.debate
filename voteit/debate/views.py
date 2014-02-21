import csv
import StringIO
from decimal import Decimal
from datetime import timedelta

import deform
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid.response import Response
from pyramid.renderers import render
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.traversal import find_interface
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent import view_action
from voteit.irl.models.interfaces import IParticipantNumbers
from voteit.core.views.base_view import BaseView
from voteit.core.views.meeting import MeetingView
from voteit.core.views.api import APIView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.schemas.common import add_csrf_token
from voteit.core import security
from voteit.core.fanstaticlib import (voteit_main_css,
                                      jquery_deform)
from voteit.core.views.components.tabs_menu import render_tabs_menu
from voteit.core.views.components.tabs_menu import generic_tab_any_querystring

from .fanstaticlib import voteit_debate_manage_speakers_js
from .fanstaticlib import voteit_debate_speaker_view_styles
from .fanstaticlib import voteit_debate_fullscreen_speakers_js
from .fanstaticlib import voteit_debate_fullscreen_speakers_css
from .fanstaticlib import voteit_debate_user_speaker_js
from .fanstaticlib import voteit_debate_user_speaker_css

from .interfaces import ISpeakerLists
from .models import get_speaker_list_plugins
from .models import populate_from_proposals
from . import DebateTSF as _


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

    def _api(self):
        return APIView(self.context, self.request)


@view_defaults(context = IMeeting, name = "speaker_list_action", permission = security.MODERATE_MEETING, renderer = 'json')
class ListActions(BaseActionView):

    def _tmp_redirect_url(self):
        #FIXME: Remove this, all functions should load via js / json
        url = self.request.resource_url(self.context, self.ai_name, 'manage_speaker_list')
        return HTTPFound(location = url)

    @view_config(request_param = "action=add")
    def add(self):
        ai = self.get_ai()
        if ai:
            self.slists.add_contextual_list(ai)
            self.success()
        return self.response

    @view_config(request_param = "action=set_state")
    def set_state(self):
        #FIXME: proper js function
        state = self.request.params.get('state')
        if state:
            self.action_list.state = state
            self.success()
        return self._tmp_redirect_url()

    @view_config(request_param = "action=delete")
    def delete(self):
        #FIXME: proper js function
        if self.list_name in self.slists:
            del self.slists[self.list_name]
            self.success()
        return self._tmp_redirect_url()

    @view_config(request_param = "action=rename")
    def rename(self):
        new_name = self.request.params.get('list_title_rename')
        if new_name:
            self.action_list.title = new_name
            self.success()
        return self.response

    @view_config(request_param = "action=active")
    def active(self):
        #FIXME: proper js function
        if self.list_name in self.slists:
            self.slists.active_list_name = self.list_name
            self.success()
        return self._tmp_redirect_url()

    @view_config(request_param = "action=undo")
    def undo(self):
        if self.action_list.speaker_undo() is not None:
            self.success()
        return self.response

    @view_config(request_param = "action=shuffle")
    def shuffle(self):
        self.action_list.shuffle()
        self.success()
        return self.response

    @view_config(request_param = "action=clear")
    def clear(self):
        self.action_list.speaker_log.clear()
        self.success()
        return self.response

    @view_config(request_param = "action=populate_from_proposals")
    def populate_from_proposals(self):
        result = populate_from_proposals(self.action_list)
        msg = _(u"Added ${count} speakers from published proposals in this context.",
                                     mapping = {'count': result})
        self.response['message'] = msg
        self.success()
        #FIXME: Remove this
        api = self._api()
        api.flash_messages.add(msg)
        return self._tmp_redirect_url()


@view_defaults(context = IMeeting, name = "speaker_action", permission = security.MODERATE_MEETING, renderer = "json")
class SpeakerActions(BaseActionView):

    def _get_pn(self):
        pn = self.request.params.get('pn', None)
        if pn:
            pn = int(pn)
            if pn in self.participant_numbers.number_to_userid:
                return pn

    @view_config(request_param = "action=add")
    def add(self):
        api = self._api()
        form = get_add_speaker_form(api, self.list_name)
        controls = self.request.POST.items()
        try:
            appstruct = form.validate(controls)
        except deform.ValidationFailure, e:
            #There's only one field with validation. Change otherwise
            api = self._api()
            self.response['message'] = api.translate(e.field['pn'].errormsg)
            return self.response
        pn = appstruct['pn']
        if pn in self.action_list.speakers:
            #Shouldn't happen since js handles this
            self.response['message'] = _(u"Already in list")
            return self.response
        if pn in self.participant_numbers.number_to_userid:
            self.action_list.add(pn, override = True)
            self.success()
        else:
            self.response['message'] = _("No user with that number")
        return self.response

    @view_config(request_param = "action=active")
    def active(self):
        pn = self._get_pn()
        if pn is None and len(self.action_list.speakers) > 0:
            pn = self.action_list.speakers[0]
        if pn is not None and self.action_list.speaker_active(pn) is not None:
            self.success()
            userid = self.participant_numbers.number_to_userid.get(pn)
            self.response['active_speaker'] = speaker_item_moderator(pn, self._api(), self.action_list, userid = userid)
        return self.response

    @view_config(request_param = "action=remove")
    def remove(self):
        pn = self._get_pn()
        if pn in self.action_list.speakers:
            self.action_list.speakers.remove(pn)
            self.success()
        return self.response

    @view_config(request_param = "action=finished")
    def finished(self):
        pn = self.action_list.current
        seconds = int(self.request.params['seconds'])
        if self.action_list.speaker_finished(pn, seconds) is not None:
            self.success()
        return self.response


def get_add_speaker_form(api, list_name):
    schema = createSchema('AddSpeakerSchema')
    schema = schema.bind(context = api.context, request = api.request, api = api)
    action_url = api.request.resource_url(api.meeting, 'speaker_action',
                                          query = {'action': 'add', 'list_name': list_name})
    return deform.Form(schema, action = action_url, buttons = (deform.Button('add', _(u"Add")),), formid = "add_speaker")


def speaker_item_moderator(pn, api, slist, userid = None):
    use_lists = slist.settings['speaker_list_count']
    safe_positions = slist.settings['safe_positions']
    response = {}
    if userid:
        response['user_info'] = api.get_creators_info([userid], portrait = False)
    else:
        response['user_info'] = _(u"(No user associated)")
    response['slist'] = slist
    response['api'] = api
    response['pn'] = pn
    response['is_active'] = pn == slist.current
    response['is_locked'] = pn in slist.speakers and slist.speakers.index(pn) < safe_positions
    return render("templates/speaker_item.pt", response, request = api.request)

def speaker_list_controls_moderator(api, slists, context):
    assert IAgendaItem.providedBy(context)
    response = {}
    response['api'] = api
    response['context'] = context
    response['active_list'] = slists.get(slists.active_list_name)
    response['context_lists'] = slists.get_contextual_lists(context)
    return render("templates/speaker_list_controls_moderator.pt", response, request = api.request)


@view_defaults(context = IMeeting, permission = security.MODERATE_MEETING)
class ManageSpeakerList(BaseView):

    @reify
    def slists(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerLists)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.api.meeting, IParticipantNumbers)

    @reify
    def active_list(self):
        return self.slists.get(self.slists.active_list_name)

    def get_add_form(self):
        return get_add_speaker_form(self.api, self.slists.active_list_name)

    @view_config(name = "manage_speaker_list", context = IAgendaItem, permission = security.MODERATE_MEETING,
                 renderer = "templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        voteit_debate_speaker_view_styles.need()
        if self.active_list:
            self.response['add_form'] = self.get_add_form().render()
        else:
            self.response['add_form'] = u""
        self.response['context_active'] = self.slists.active_list_name in self.slists.get_contexual_list_names(self.context)
        self.response['active_list'] = self.slists.get(self.slists.active_list_name)
        self.response['speaker_item'] = self.speaker_item
        self.response['speaker_list_controls'] = speaker_list_controls_moderator(self.api, self.slists, self.api.context)
        return self.response

    @view_config(name = "_speaker_queue_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_queue_moderator.pt")
    def speaker_queue_moderator(self):
        self.response['active_list'] = self.active_list
        self.response['speaker_item'] = self.speaker_item
        self.response['use_lists'] = self.api.meeting.get_field_value('speaker_list_count', 1)
        self.response['safe_pos'] = self.api.meeting.get_field_value('safe_positions', 0)
        return self.response

    @view_config(name = "_speaker_log_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_log_moderator.pt")
    def speaker_log_moderator(self):
        self.response['active_list'] = self.active_list
        number_to_profile_tag = {}
        for pn in self.active_list.speaker_log.keys():
            if pn in self.participant_numbers.number_to_userid:
                userid = self.participant_numbers.number_to_userid[pn]
                number_to_profile_tag[pn] = self.api.get_creators_info([userid], portrait = False)
            else:
                number_to_profile_tag[pn] = pn
        self.response['number_to_profile_tag'] = number_to_profile_tag
        self.response['format_secs'] = self.format_seconds
        return self.response

    @view_config(name = "_speaker_lists_moderator", context = IAgendaItem, permission = security.MODERATE_MEETING)
    def speaker_lists(self):
        if self.request.is_xhr:
            return Response(speaker_list_controls_moderator(self.api, self.slists, self.api.context))
        #Fallback in case of js error
        return HTTPFound(location = self.request.resource_url(self.context, 'manage_speaker_list'))

    def speaker_item(self, pn):
        userid = self.participant_numbers.number_to_userid.get(int(pn))
        return speaker_item_moderator(pn, self.api, self.active_list, userid = userid)

    @view_config(name = "edit_speaker_log", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer="voteit.core.views:templates/base_edit.pt")
    def edit_speaker_log(self):
        """ Edit log entries for a specific speaker. """
        speaker_list_name = self.request.GET['speaker_list']
        speaker_list = self.slists.speaker_lists[speaker_list_name]
        speaker = int(self.request.GET['speaker'])
        schema = createSchema("EditSpeakerLogSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        form = deform.Form(schema, buttons = (deform.Button("save", _(u"Save")), deform.Button("cancel", _(u"Cancel"))))
        post = self.request.POST
        if self.request.method == 'POST':
            if 'save' in post:
                controls = post.items()
                try:
                    appstruct = form.validate(controls)
                except deform.ValidationFailure, e:
                    self.response['form'] = e.render()
                    return self.response
                del speaker_list.speaker_log[speaker][:]
                speaker_list.speaker_log[speaker].extend(appstruct['logs'])
            ai = find_interface(speaker_list, IAgendaItem)
            url = self.request.resource_url(ai, 'manage_speaker_list')
            return HTTPFound(location = url)
        appstruct = {'logs': speaker_list.speaker_log[speaker]}
        self.response['form'] = form.render(appstruct = appstruct)
        return self.response

    def format_seconds(self, secs):
        val = str(timedelta(seconds=int(secs)))
        try:
            return ":".join([x for x in val.split(':') if int(x)])
        except ValueError:
            return val


class SpeakerSettingsView(MeetingView):

    @view_config(context=IMeeting, name="speaker_list_settings", renderer="voteit.core.views:templates/base_edit.pt",
                 permission=security.MODERATE_MEETING)
    def speaker_list_settings(self):
        schema = createSchema("SpeakerListSettingsSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_speaker_lists')
        return self.form(schema)

    @view_config(context=IMeeting, name="speaker_list_plugin", renderer="voteit.core.views:templates/base_edit.pt",
                 permission=security.MODERATE_MEETING)
    def speaker_list_plugin(self):
        schema = createSchema("SpeakerListPluginSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        self.response['tabs'] = self.api.render_single_view_component(self.context, self.request, 'tabs', 'manage_speaker_lists')
        return self.form(schema)


class FullscreenSpeakerList(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(name = "fullscreen_speaker_list", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/fullscreen_view.pt")
    def fullscreen_view(self):
        voteit_main_css.need()
        jquery_deform.need()
        voteit_debate_fullscreen_speakers_js.need()
        voteit_debate_fullscreen_speakers_css.need()
        response = dict()
        return response

    @view_config(name = "_fullscreen_list", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/fullscreen_list.pt")
    def fullscreen_list(self):
        slists = self.request.registry.getAdapter(self.context, ISpeakerLists)
        participant_numbers = self.request.registry.getAdapter(self.context, IParticipantNumbers)
        root = self.context.__parent__
        active_list = slists.get(slists.active_list_name)
        active_speaker = None
        speaker_profiles = []
        num_lists = self.context.get_field_value('speaker_list_count', 1)
        if active_list:
            if active_list.current != None: #Note could be int 0!
                userid = participant_numbers.number_to_userid[active_list.current]
                active_speaker = root.users[userid]
            for num in active_list.speakers:
                userid = participant_numbers.number_to_userid.get(num)
                if userid:
                    speaker_profiles.append(root.users[userid])

        def _get_user_list_number(userid):
            pn = participant_numbers.userid_to_number[userid]
            return active_list.get_number_for(pn)

        response = dict(
            active_list = active_list,
            active_speaker = active_speaker,
            speaker_profiles = speaker_profiles,
            get_user_list_number = _get_user_list_number,
            userid_to_number = participant_numbers.userid_to_number, #FIXME: This shouldn't be needed, refactor later
        )
        return response


class UserSpeakerLists(BaseView):

    @reify
    def slists(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerLists)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.api.meeting, IParticipantNumbers)

    @view_config(name = "_user_speaker_lists", context = IAgendaItem, permission = security.VIEW,
                 renderer = "templates/user_speaker.pt")
    def view(self):
        action = self.request.GET.get('action', None)
        pn = self.participant_numbers.userid_to_number.get(self.api.userid, None)
        use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
        safe_pos = self.api.meeting.get_field_value('safe_positions', 0)
        max_times_in_list = self.api.meeting.get_field_value('max_times_in_list', 0)
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
        self.response['speaker_lists'] = self.slists.get_contextual_lists(self.context)
        self.response['active_list'] = self.slists.get(self.slists.active_list_name)
        self.response['pn'] = pn
        self.response['use_lists'] = use_lists
        self.response['safe_pos'] = safe_pos
        self.response['over_limit'] = _over_limit
        self.response['max_times_in_list'] = max_times_in_list
        if pn != None:
            def _show_add(sl, pn):
                return pn != None and sl.state == 'open' and pn not in sl.speakers
            self.response['show_add'] = _show_add
        return self.response

    @view_config(name = "speaker_statistics", context = IMeeting, permission = security.VIEW,
                 renderer = "templates/speaker_statistics.pt")
    def speaker_statistics_view(self):
        self.response['number_to_userid'] = self.participant_numbers.number_to_userid
        results = {}
        maxval = 0
        for sl in self.slists.speaker_lists.values():
            for (pn, entries) in sl.speaker_log.items():
                current = results.setdefault(pn, [])
                current.extend(entries)
                this_val = sum(current)
                if this_val > maxval:
                    maxval = this_val
        self.response['results'] = [(x, results[x]) for x in sorted(results)]

        def _get_percentage(num):
            try:
                return int(round(Decimal(num) / maxval * 100))
            except:
                return u"0%"

        self.response['get_perc'] = _get_percentage
        return self.response

    @view_config(name='speaker_statistics.csv', context=IMeeting, permission=security.VIEW)
    def export(self):
        output = StringIO.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([self.context.title.encode('utf-8')])
        writer.writerow([self.api.translate(_(u"Speaker statistics"))])
        writer.writerow(["#", self.api.translate(_(u"Seconds"))])
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
        response = Response(content_type='text/csv',
                            body=contents)
        return response


@view_action('meeting', 'fullscreen_speaker_list', title = _(u"Speaker list for projectors"),
             permission = security.MODERATE_MEETING, link = 'fullscreen_speaker_list')
@view_action('meeting', 'speaker_statistics', title = _(u"Speaker statistics"),
             permission = security.VIEW, link = 'speaker_statistics')
@view_action('settings_menu', 'speaker_list_settings', title = _(u"Speaker list settings"),
             permission = security.MODERATE_MEETING, link = 'speaker_list_settings')
def meeting_context_menu_item(context, request, va, **kw):
    api = kw['api']
    url = "%s%s" % (api.meeting_url, va.kwargs['link'])
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('context_actions', 'manage_speaker_list', title = _(u"Manage speaker list"),
             interface = IAgendaItem)
def manage_speaker_list_menu(context, request, va, **kw):
    api = kw['api']
    url = u"%s%s" % (request.resource_url(context), 'manage_speaker_list')
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('agenda_item_top', 'user_speaker_list')
def user_speaker_list(context, request, *args, **kw):
    api = kw['api']
    if not api.meeting.get_field_value('show_controls_for_participants', False):
        return u""
    if context.get_workflow_state() not in (u'upcoming', u'ongoing'):
        return u""
    response = dict()
    response.update(kw)
    voteit_debate_user_speaker_js.need()
    voteit_debate_user_speaker_css.need()
    return render("templates/user_speaker_area.pt", response, request = request)

@view_action('tabs', 'manage_speaker_lists', permission = security.MODERATE_MEETING)
def render_tabs_menu_sl(context, request, va, **kw):
    return render_tabs_menu(context, request, va, **kw)

@view_action('manage_speaker_lists', 'speaker_list_settings', permission = security.MODERATE_MEETING,
             title = _(u"Settings"), link = u'speaker_list_settings')
def manage_speaker_lists_tabs(context, request, va, **kw):
    return generic_tab_any_querystring(context, request, va, **kw)

@view_action('manage_speaker_lists', 'speaker_list_plugin', title = _(u"Speaker list plugin"),
             permission = security.MODERATE_MEETING, link = 'speaker_list_plugin')
def speaker_list_handlers_menu_item(context, request, va, **kw):
    return generic_tab_any_querystring(context, request, va, **kw)
