# -*- coding: utf-8 -*-

from arche.views.base import BaseView
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
from voteit.core.models.interfaces import IMeeting
from voteit.irl.models.interfaces import IParticipantNumbers

from voteit.debate.fanstaticlib import fullscreen_static
from voteit.debate.interfaces import ISpeakerLists


@view_defaults(context=IMeeting)
class FullscreenSpeakerList(BaseView):
    @view_config(name="fullscreen_speaker_list",
                 permission=NO_PERMISSION_REQUIRED,
                 renderer="voteit.debate:templates/fullscreen_view.pt")
    def fullscreen_view(self):
        fullscreen_static.need()
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


def includeme(config):
    config.scan(__name__)
