# -*- coding: utf-8 -*-

import colander
from arche.interfaces import ISchemaCreatedEvent

from voteit.debate import _
from voteit.debate.schemas import SpeakerListSettingsSchema


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


def includeme(config):
    config.add_subscriber(update_schema, [SpeakerListSettingsSchema, ISchemaCreatedEvent])
