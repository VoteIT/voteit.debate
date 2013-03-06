import deform
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.views.api import APIView
from voteit.core import security

from .fanstaticlib import voteit_debate_manage_speakers_js
from .interfaces import ISpeakerListHandler


class ManageSpeakerList(BaseView):

    @reify
    def sl_handler(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerListHandler)

    def get_userid_form(self):
        schema = createSchema('AddSpeakerSchema')
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        action_url = self.request.resource_url(self.api.meeting, '_add_speaker')
        return deform.Form(schema, action = action_url, buttons = (), formid = "add_speaker")

    @view_config(name = "manage_speaker_list", context = IAgendaItem, permission = security.MODERATE_MEETING,
                 renderer = "templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        self.sl_handler.active_ai(self.context)
        self.response['userid_form'] = self.get_userid_form().render()
        return self.response

    @view_config(name = "_add_speaker", context = IMeeting, permission = security.MODERATE_MEETING)
    def add_speaker(self):
        form = self.get_userid_form()
        controls = self.request.POST.items()
        sl = self.sl_handler.get_active_list()
        if not sl:
            return HTTPForbidden()
        try:
            appstruct = form.validate(controls)
        except deform.ValidationFailure, e:
            return HTTPForbidden()
        sl.add(appstruct['userid'])
        return Response()

    @view_config(name = '_remove_speaker', context = IMeeting, permission = security.MODERATE_MEETING)
    def remove_speaker(self):
        index = int(self.request.GET.get('index'))
        sl = self.sl_handler.get_active_list()
        sl.remove(index)
        return Response()

    @view_config(name = "_speaker_listing_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_listing_moderator.pt")
    def speaker_listing_moderator(self):
        self.response['speaker_list'] = self.sl_handler.get_active_list()
        return self.response
