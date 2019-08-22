# -*- coding: utf-8 -*-
from collections import Counter

import colander
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from BTrees.IOBTree import IOSet
from arche.interfaces import ISchemaCreatedEvent
from pyramid.decorator import reify
from voteit.irl.models.interfaces import IParticipantNumbers

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
    tpl_user = 'voteit.debate:plugins/global_lists/templates/snippets/speaker_item_user.pt'

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

    # Old method
    # def get_time_restr(self, num):
    #     if self.time_restrictions:
    #         try:
    #             return self.time_restrictions[num]
    #         except IndexError:
    #             return self.time_restrictions[-1]

    def get_time_restriction(self, sl, pn):
        try:
            return self.restrictions_active[sl.name][pn]
        except KeyError:
            pass

    def get_annotation(self, name, cls=OOBTree):
        # Avoid creating new OOBTree objects if they don't exist
        attr = '__global_time__' + name
        annotation = getattr(self.context, attr, None)
        if not isinstance(annotation, cls):
            annotation = cls()
            setattr(self.context, attr, annotation)
        return annotation

    @reify
    def restrictions_active(self):
        # type: () -> OOBTree
        return self.get_annotation('restrictions_active')

    @reify
    def restrictions_used(self):
        # type: () -> IOBTree
        return self.get_annotation('restrictions_used', IOBTree)

    def get_available_restrictions(self, pn=None):
        # type: (int) -> list
        if pn is None:
            pns = IParticipantNumbers(self.context)
            pn = pns.userid_to_number.get(self.request.authenticated_userid)
            assert pn is not None, 'Can\'t get available restrictions for user w/o participant number.'
        active = set(item[pn] for item in self.restrictions_active.values() if pn in item)
        used = self.restrictions_used.get(pn, ())
        non_avail = active.union(used)
        return [r for r in self.time_restrictions[:-1] if r not in non_avail] + self.time_restrictions[-1:]

    def _remove_active(self, sl, pn, used=False):
        try:
            if used:
                self.restrictions_used.setdefault(pn, IOSet()).add(self.restrictions_active[sl.name][pn])
            del self.restrictions_active[sl.name][pn]
        except KeyError:
            pass

    def add_to_list(self, pn, sl, override=False):
        user_available = self.get_available_restrictions(pn)
        try:
            restriction = int(self.request.params.get('timeRestriction'))
            # If client sent non-available restriction, use first available instead of failing.
            if restriction not in user_available:
                raise ValueError
        except (TypeError, ValueError):
            restriction = user_available[0]

        count = super(GlobalLists, self).add_to_list(pn, sl, override)
        self.restrictions_active.setdefault(sl.name, OOBTree())[pn] = restriction
        return count

    def remove_from_list(self, pn, sl):
        super(GlobalLists, self).remove_from_list(pn, sl)
        self._remove_active(sl, pn)

    def finish_on_list(self, sl):
        pn = super(GlobalLists, self).finish_on_list(sl)
        self._remove_active(sl, pn, used=True)
        return pn


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
    config.registry.registerAdapter(GlobalLists, name=GlobalLists.name)
    config.add_subscriber(update_schema, [SpeakerListSettingsSchema, ISchemaCreatedEvent])
