# -*- coding: utf-8 -*-
from collections import Counter

import colander
from arche.interfaces import ISchemaCreatedEvent
from pyramid.decorator import reify
from pyramid.events import subscriber

from voteit.debate import _
from voteit.debate.events import SpeakerAddedEvent, SpeakerRemovedEvent, SpeakerFinishedEvent
from voteit.debate.models import SpeakerLists
from voteit.debate.schemas import SpeakerListSettingsSchema


class GlobalLists(SpeakerLists):
    """ Special version that takes care of total time consumed """
    name = "global_lists"
    title = _("Global timelog")
    description = _("Monitors and shows total entries")
    tpl_manage_speaker_item = 'voteit.debate:plugins/global_lists/templates/manage_speaker_item.pt'

    def total_count(self, pns):
        # FIXME: Should be cached later on
        counter = Counter()
        for sl in self.values():
            for (k, v) in sl.speaker_log.items():
                if k in pns:
                    counter.update({k: len(v)})
        return counter

    @reify
    def time_restrictions(self):
        return self.settings.get('global_time_restrictions', ())

    def get_time_restr(self, num):
        if self.time_restrictions:
            try:
                return self.time_restrictions[num]
            except IndexError:
                return self.time_restrictions[-1]


def update_schema(schema, event):
    request = event.request
    if request.speaker_lists.name != 'global_lists':
        return
    schema.add(
        colander.SchemaNode(
            colander.Sequence(),
            colander.SchemaNode(
                colander.Int(),
                title = _("minute restriction"),
                name='foo',  # Not used
            ),
            title=_("Speaker time global entries"),
            description=_(
                "speaker_time_global_entries_description",
                default="Add entries to show time restriction. "
                        "No entries mean no restriction. "
                        "If you add entries, they will be shown in sequence."
                        "The last one will be used for anyone "
                        "above the number of entries. "
                        "So 2 rows with 2 and then 1 would mean 2 minutes "
                        "for first entry, and 1 minute for all other entries."
            ),
            name='global_time_restrictions',
            missing=(),
            tab='advanced',
        )
    )


def test(event):
    print('yey')
    print(event.context)
    print(event.pn)


def includeme(config):
    config.registry.registerAdapter(GlobalLists, name=GlobalLists.name)
    config.add_subscriber(update_schema, [SpeakerListSettingsSchema, ISchemaCreatedEvent])
    config.add_subscriber(test, SpeakerAddedEvent)
