import deform
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.renderers import render
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema
from voteit.irl.models.interfaces import IParticipantNumbers
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core import security

from .fanstaticlib import voteit_debate_manage_speakers_js
from .fanstaticlib import voteit_debate_speaker_view_styles
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
        self.response['active_list'] = self.active_list
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
        sl.add(pn)
        return Response(self.speaker_item(pn))

    @view_config(name = '_remove_speaker', context = IMeeting, permission = security.MODERATE_MEETING)
    def remove_speaker(self):
        pn = int(self.request.GET.get('pn'))
        sl = self.active_list
        sl.remove(pn)
        return Response()

    @view_config(name = '_set_speaker_order', context = IMeeting, permission = security.MODERATE_MEETING)
    def set_speaker_order(self):
        sl = self.active_list
        post = self.request.POST.dict_of_lists()
        sl.set(post['speaker_id'])
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

    @view_config(name = "_speaker_finished", context = IMeeting, permission = security.MODERATE_MEETING)
    def speaker_finished(self):
        seconds = self.request.GET['seconds']
        speaker_id = int(self.request.GET['speaker_id'])
        sl = self.active_list
        sl.speaker_finished(speaker_id, seconds)
        return Response(render("templates/speaker_log_moderator.pt", self.speaker_log_moderator(), request = self.request))

    def speaker_item(self, pn):
        self.response['pn'] = pn
        userid = self.participant_numbers.number_to_userid[int(pn)]
        self.response['user_info'] = self.api.get_creators_info([userid], portrait = False)
        return render("templates/speaker_item.pt", self.response, request = self.request)
