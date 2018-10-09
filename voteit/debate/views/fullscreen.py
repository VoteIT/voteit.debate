# -*- coding: utf-8 -*-
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPBadRequest
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
        categories = self.settings.get('multiple_lists', ())
        category_users = self.settings.get('category_users', {})
        current_category = self.request.GET.get('category')
        _next = None
        previous = None
        if categories:
            if current_category is None:
                for cat in categories:
                    if self.request.authenticated_userid in category_users[cat]:
                        current_category = cat
            if current_category is None:
                current_category = categories[0]

            try:
                current_index = categories.index(current_category)
            except ValueError:
                raise HTTPBadRequest(_('No speaker list "${name}" found.', mapping={'name': current_category}))
            if current_index > 0:
                previous = categories[current_index-1]
            if current_index < len(categories)-1:
                _next = categories[current_index+1]

        return {
            'inactive_list_title': _("No list active"),
            'categories': categories,
            'current_category': current_category,
            'next_category': _next,
            'previous_category': previous,
        }


def includeme(config):
    config.scan(__name__)
