from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from voteit.core.models.interfaces import IAgendaItem
from voteit.irl.models.interfaces import IParticipantNumbers

from voteit.debate import _


class DebatePortlet(PortletType):
    name = "voteit_debate"
    title = _("Debate")
    tpl = "voteit.debate:templates/portlet.pt"

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            pns = IParticipantNumbers(request.meeting, None)
            pn = None
            if pns:
                pn = pns.userid_to_number.get(request.authenticated_userid, None)
            update_interv = request.speaker_lists.settings.get('user_update_interval', 5)
            join_schema = request.get_schema(request.profile, 'SpeakerLists', 'user_join_speaker_list')
            join_schema_active = any(not hasattr(request.profile, f.name) for f in join_schema.children)
            return render(self.tpl,
                          {'portlet': self.portlet,
                           'view': view,
                           'user_update_interval': update_interv,
                           'pn': pn,
                           'user_join_schema_active': join_schema_active},
                          request=request)


def includeme(config):
    config.add_portlet(DebatePortlet)
