# -*- coding: utf-8 -*-
from collections import Counter

from voteit.debate.models import SpeakerLists
from voteit.debate import _


class GlobalLists(SpeakerLists):
    """ Special version that takes care of total time consumed """
    name = "global_lists"
    title = _("Global timelog")
    description = _("Monitors and shows total entries")
    tpl_manage_speaker_item = 'voteit.debate:plugins/global_lists/templates/manage_speaker_item.pt'
    #tpl_user = 'voteit.debate:templates/snippets/speaker_item_user.pt'

    def total_count(self, pns):
        # FIXME: Should be cached later on
        counter = Counter()
        for sl in self.values():
            for (k, v) in sl.speaker_log.items():
                if k in pns:
                    counter.update({k: len(v)})
        return counter


def includeme(config):
    config.registry.registerAdapter(GlobalLists, name=GlobalLists.name)
