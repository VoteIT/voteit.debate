from __future__ import unicode_literals

from arche.portlets import PortletType
from pyramid.renderers import render
from voteit.core.models.interfaces import IAgendaItem

from voteit.debate import _


class DebatePortlet(PortletType):
    name = "voteit_debate"
    title = _("Debate")

    def render(self, context, request, view, **kwargs):
        if IAgendaItem.providedBy(context):
            return render("voteit.debate:templates/portlet.pt",
                          {'portlet': self.portlet, 'view': view},
                          request = request)


def includeme(config):
    config.add_portlet(DebatePortlet)
