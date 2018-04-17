from arche.portlets import get_portlet_manager
from arche.views.base import DefaultEditForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from voteit.core import security
from voteit.core.models.interfaces import IMeeting

from voteit.debate import _
from voteit.debate.interfaces import ISpeakerListSettings


@view_config(context=IMeeting,
             name="speaker_list_settings",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class SpeakerListSettingsForm(DefaultEditForm):
    schema_name = 'settings'
    type_name = 'SpeakerLists'
    title = _("Speaker list settings")

    @reify
    def settings(self):
        return ISpeakerListSettings(self.context)

    def appstruct(self):
        return dict(self.settings)

    def save_success(self, appstruct):
        self.settings.update(appstruct)
        self.toggle_portlet(appstruct['enable_voteit_debate'])
        self.flash_messages.add(self.default_success, type="success")
        return HTTPFound(location=self.request.resource_url(self.context))

    def toggle_portlet(self, enable=True):
        manager = get_portlet_manager(self.context)
        current = manager.get_portlets('agenda_item', 'voteit_debate')
        if not enable:
            for portlet in current:
                manager.remove('agenda_item', portlet.uid)
        else:
            if not current:
                new_portlet = manager.add('agenda_item', 'voteit_debate')
                ai_slot = manager['agenda_item']
                current_order = list(ai_slot.keys())
                pos = current_order.index(new_portlet.uid)
                #Find a good position to insert it - above discussions or proposals
                types = ('ai_proposals', 'ai_discussions')
                for portlet in ai_slot.values():
                    if portlet.portlet_type in types:
                        pos = current_order.index(portlet.uid)
                        break
                current_order.remove(new_portlet.uid)
                current_order.insert(pos, new_portlet.uid)
                ai_slot.order = current_order


def includeme(config):
    config.scan(__name__)
