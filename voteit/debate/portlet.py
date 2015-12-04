from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from voteit.core.models.interfaces import IAgendaItem

from voteit.debate import _
from voteit.debate.fanstaticlib import voteit_debate_user_speaker_js
from voteit.debate.fanstaticlib import voteit_debate_user_speaker_css


class DebatePortlet(PortletType):
    name = "voteit_debate"
    title = _("Debate")

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            voteit_debate_user_speaker_js.need()
            voteit_debate_user_speaker_css.need()
            return render("voteit.debate:templates/portlet.pt",
                          {'portlet': self.portlet, 'view': view},
                          request = request)


def includeme(config):
    config.add_portlet(DebatePortlet)
