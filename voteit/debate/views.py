import deform
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.renderers import render
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent import view_action
from voteit.irl.models.interfaces import IParticipantNumbers
from voteit.core.views.base_view import BaseView
from voteit.core.views.meeting import MeetingView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.schemas.common import add_csrf_token
from voteit.core import security
from voteit.core.fanstaticlib import (voteit_main_css,
                                      jquery_deform)

from .fanstaticlib import voteit_debate_manage_speakers_js
from .fanstaticlib import voteit_debate_speaker_view_styles
from .fanstaticlib import voteit_debate_fullscreen_speakers_js
from .fanstaticlib import voteit_debate_fullscreen_speakers_css
from .fanstaticlib import voteit_debate_user_speaker_js
from .fanstaticlib import voteit_debate_user_speaker_css

from .interfaces import ISpeakerListHandler
from . import DebateTSF as _


class ManageSpeakerList(BaseView):

    @reify
    def sl_handler(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerListHandler)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.api.meeting, IParticipantNumbers)

    @reify
    def active_list(self):
        return self.sl_handler.get_active_list()

    def get_add_form(self):
        schema = createSchema('AddSpeakerSchema')
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        action_url = self.request.resource_url(self.api.meeting, 'speaker_action',
                                               query = {'action': 'add', 'list_name': self.active_list.name})
        return deform.Form(schema, action = action_url, buttons = (deform.Button('add', _(u"Add")),), formid = "add_speaker")

    @view_config(name = "manage_speaker_list", context = IAgendaItem, permission = security.MODERATE_MEETING,
                 renderer = "templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        voteit_debate_speaker_view_styles.need()
        if self.active_list:
            self.response['add_form'] = self.get_add_form().render()
        else:
            self.response['add_form'] = u""
        self.response['context_lists'] = self.sl_handler.get_contextual_lists(self.context)
        self.response['context_active'] = self.active_list in self.response['context_lists']
        self.response['active_list'] = self.active_list
        self.response['speaker_item'] = self.speaker_item
        return self.response

    @view_config(name = "speaker_list_action", context = IAgendaItem, permission = security.MODERATE_MEETING)
    def list_action(self):
        action = self.request.GET['action']
        if action == 'add':
            self.sl_handler.add_contextual_list(self.context)
        if action == 'remove':
            name = self.request.GET['name']
            self.sl_handler.remove_list(name)
        if action == 'set':
            name = self.request.GET['name']
            self.sl_handler.set_active_list(name)
        if action == 'clear':
            name = self.request.GET['name']
            self.active_list.speaker_log.clear()
        if action == 'rename':
            name = self.request.GET['name']
            #FIXME: Escape title?
            self.sl_handler.speaker_lists[name].title = self.request.GET['list_title_rename']
            return Response(self.request.GET['list_title_rename'])
        return HTTPFound(location = self.request.resource_url(self.context, "manage_speaker_list"))

    @view_config(name = "speaker_action", context = IMeeting, permission = security.MODERATE_MEETING)
    def speaker_action(self):
        action = self.request.GET['action']
        if self.request.GET['list_name'] != self.active_list.name:
            return HTTPForbidden()
        if action == 'active':
            speaker_name = self.request.GET.get('name', None) #Specific speaker, or simply top of the list
            if speaker_name == None:
                if self.active_list.speakers:
                    speaker_name = self.active_list.speakers[0]
                else:
                    raise HTTPForbidden()
            self.active_list.speaker_active(speaker_name)
            return Response(self.speaker_item(speaker_name))
        if action == 'finished':
            seconds = int(self.request.GET['seconds'])
            self.active_list.speaker_finished(seconds)
            return Response(render("templates/speaker_log_moderator.pt", self.speaker_log_moderator(), request = self.request))
        if action == 'remove':
            speaker_name = int(self.request.GET['name'])
            self.active_list.remove(speaker_name)
            return Response()
        if action == 'add':
            form = self.get_add_form()
            controls = self.request.POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                return HTTPForbidden()
            pn = appstruct['pn']
            if pn in self.active_list.speakers:
                return HTTPForbidden()
            if pn in self.participant_numbers.number_to_userid:
                use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
                self.active_list.add(pn, use_lists = use_lists)
                return Response()
        return HTTPForbidden()

    @view_config(name = "_speaker_queue_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_queue_moderator.pt")
    def speaker_queue_moderator(self):
        if not self.active_list:
            return u""
        self.response['speaker_list'] = self.active_list
        self.response['speaker_item'] = self.speaker_item
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
        return self.response

    def speaker_item(self, pn):
        self.response['pn'] = pn
        userid = self.participant_numbers.number_to_userid[int(pn)]
        self.response['user_info'] = self.api.get_creators_info([userid], portrait = False)
        self.response['active_list'] = self.active_list
        return render("templates/speaker_item.pt", self.response, request = self.request)


class SpeakerSettingsView(MeetingView):

    @view_config(context=IMeeting, name="speaker_list_settings", renderer="voteit.core.views:templates/base_edit.pt",
                 permission=security.MODERATE_MEETING)
    def speaker_list_settings(self):
        schema = createSchema("SpeakerListSettingsSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
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
        sl_handler = self.request.registry.getAdapter(self.context, ISpeakerListHandler)
        participant_numbers = self.request.registry.getAdapter(self.context, IParticipantNumbers)
        root = self.context.__parent__
        active_list = sl_handler.get_active_list()
        num_lists = self.context.get_field_value('speaker_list_count', 1)
        speaker_profiles = []
        if active_list.current != None: #Note could be int 0!
            userid = participant_numbers.number_to_userid[active_list.current]
            speaker_profiles.append(root.users[userid])
        for num in active_list.speakers:
            userid = participant_numbers.number_to_userid[num]
            speaker_profiles.append(root.users[userid])

        def _get_user_list_number(userid):
            num = participant_numbers.userid_to_number[userid]
            spoken_times = len(active_list.speaker_log.get(num, ())) + 1
            return spoken_times <= num_lists and spoken_times or num_lists

        response = dict(
            active_list = active_list,
            speaker_profiles = speaker_profiles,
            get_user_list_number = _get_user_list_number,
        )
        return response


class UserSpeakerLists(BaseView):

    @reify
    def sl_handler(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerListHandler)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.api.meeting, IParticipantNumbers)

    @view_config(name = "_user_speaker_lists", context = IAgendaItem, permission = security.VIEW,
                 renderer = "templates/user_speaker.pt")
    def view(self):
        action = self.request.GET.get('action', None)
        pn = self.participant_numbers.userid_to_number[self.api.userid]
        use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
        if action:
            list_name = self.request.GET.get('list_name', None)
            if list_name not in self.sl_handler.speaker_lists:
                raise HTTPForbidden(_(u"Speaker list doesn't exist"))
            sl = self.sl_handler.speaker_lists[list_name]
            if action == u'add':
                sl.add(pn, use_lists = use_lists)
            if action == u'remove':
                sl.remove(pn)
        self.response['speaker_lists'] = self.sl_handler.get_contextual_lists(self.context)
        self.response['active_list'] = self.sl_handler.get_active_list()
        self.response['pn'] = pn
        self.response['use_lists'] = use_lists
        return self.response


@view_action('meeting', 'fullscreen_speaker_list', title = _(u"Speaker list for projectors"),
             permission = security.MODERATE_MEETING, link = 'fullscreen_speaker_list')
@view_action('settings_menu', 'speaker_list_settings', title = _(u"Speaker list settings"),
             permission = security.MODERATE_MEETING, link = 'speaker_list_settings')
def meeting_context_menu_item(context, request, va, **kw):
    api = kw['api']
    url = "%s%s" % (api.meeting_url, va.kwargs['link'])
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('context_actions', 'manage_speaker_list', title = _(u"Speaker lists"),
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
    participant_numbers = request.registry.getAdapter(api.meeting, IParticipantNumbers)
    if api.userid not in participant_numbers.userid_to_number:
        return u""
    response = dict()
    response.update(kw)
    voteit_debate_user_speaker_js.need()
    voteit_debate_user_speaker_css.need()
    return render("templates/user_speaker_area.pt", response, request = request)
