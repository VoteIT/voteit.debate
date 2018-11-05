# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.decorator import reify
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
from voteit.core.models.interfaces import IMeeting

from voteit.debate.fanstaticlib import fullscreen_static
from voteit.debate import _
from voteit.debate.interfaces import ISpeakerListSettings
from voteit.debate.views.base import BaseSLView


@view_defaults(context=IMeeting)
class FullscreenSpeakerList(BaseSLView):

    @reify
    def settings(self):
        return ISpeakerListSettings(self.context)

    @view_config(name="fullscreen_speaker_list",
                 permission=NO_PERMISSION_REQUIRED,
                 renderer="voteit.debate:templates/fullscreen.pt")
    def fullscreen_view(self):
        fullscreen_static.need()
        current_category = self.request.GET.get('category', 'default')

        return {
            'inactive_list_title': _("No list active"),
            'current_category': current_category,
        }


def includeme(config):
    config.scan(__name__)
