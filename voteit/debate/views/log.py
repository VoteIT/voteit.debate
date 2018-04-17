# -*- coding: utf-8 -*-

from arche.views.base import DefaultEditForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.traversal import find_interface
from pyramid.view import view_config
from voteit.core import security
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting

from voteit.debate import _


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
        speaker_list_name = self.request.GET['speaker_list']
        return self.request.speaker_lists[speaker_list_name]

    @reify
    def users_speaker_log(self):
        pn = int(self.request.GET['pn'])
        return self.edit_list.speaker_log[pn]

    def appstruct(self):
        return {'logs': self.users_speaker_log}

    def save_success(self, appstruct):
        del self.users_speaker_log[:]
        self.users_speaker_log.extend(appstruct['logs'])
        self.flash_messages.add(self.default_success)
        return self._redirect()

    def _redirect(self):
        ai = find_interface(self.edit_list, IAgendaItem)
        url = self.request.resource_url(ai, 'manage_speaker_lists')
        return HTTPFound(location=url)

    def cancel_success(self, *args):
        return self._redirect()


def includeme(config):
    config.scan(__name__)
