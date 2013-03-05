import deform
from pyramid.view import view_config
from pyramid.response import Response
from betahaus.pyracont.factories import createSchema
from voteit.core.views.base_view import BaseView
from voteit.core.models.interfaces import IMeeting
from voteit.core import security

from .fanstaticlib import voteit_debate_manage_speakers_js


class ManageSpeakerList(BaseView):
    
    @view_config(name = "manage_speaker_list", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        userid_schema = createSchema('AddSpeakerSchema')
        userid_schema = userid_schema.bind(context = self.context, request = self.request, api = self.api)
        action_url = self.request.resource_url(self.context, '_add_speaker')
        userid_form = deform.Form(userid_schema, action = action_url, buttons = (), formid = "add_speaker")
        self.response['userid_form'] = userid_form.render()
        return self.response

    @view_config(name = "_add_speaker", context = IMeeting, permission = security.MODERATE_MEETING)
    def add_speaker(self):
        return Response()


@view_config(name = "_speaker_listing", context = IMeeting, permission = security.MODERATE_MEETING,
             renderer = "templates/speaker_listing.pt")
def speaker_data(context, request):
    response = {}
    return response
