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
        action_url = self.request.resource_url(self.api.meeting, '_add_speaker')
        return deform.Form(schema, action = action_url, buttons = (deform.Button('add', _(u"Add")),), formid = "add_speaker")

    @view_config(name = "manage_speaker_list", context = IAgendaItem, permission = security.MODERATE_MEETING,
                 renderer = "templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        voteit_debate_speaker_view_styles.need()
        self.response['add_form'] = self.get_add_form().render()
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

    @view_config(name = "_add_speaker", context = IMeeting, permission = security.MODERATE_MEETING)
    def add_speaker(self):
        form = self.get_add_form()
        controls = self.request.POST.items()
        sl = self.active_list
        #FIXME: Proper error messages
        if not sl:
            return HTTPForbidden()
        try:
            appstruct = form.validate(controls)
        except deform.ValidationFailure, e:
            return HTTPForbidden()
        pn = appstruct['pn']
        if pn in sl.speakers:
            return HTTPForbidden()
        if pn in self.participant_numbers.number_to_userid:
            sl.add(pn)
            return Response()
        return HTTPForbidden()

    @view_config(name = '_remove_speaker', context = IMeeting, permission = security.MODERATE_MEETING)
    def remove_speaker(self):
        pn = int(self.request.GET.get('pn'))
        sl = self.active_list
        sl.remove(pn)
        return Response()

    @view_config(name = "_speaker_queue_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_queue_moderator.pt")
    def speaker_queue_moderator(self):
        self.response['speaker_list'] = self.active_list
        self.response['speaker_item'] = self.speaker_item
        return self.response

    @view_config(name = "_speaker_log_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_log_moderator.pt")
    def speaker_log_moderator(self):
        self.response['speaker_list'] = self.active_list
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
