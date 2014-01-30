import colander
import deform
from betahaus.pyracont.decorators import schema_factory
from voteit.irl.schemas import deferred_autocompleting_participant_number_widget
from voteit.irl.schemas import deferred_existing_participant_number_validator

from . import DebateTSF as _
from .interfaces import ISpeakerListHandler

@schema_factory('AddSpeakerSchema')
class AddSpeakerSchema(colander.Schema):
    pn = colander.SchemaNode(colander.Int(),
                             title = _(u"Add speaker"),
                             widget = deferred_autocompleting_participant_number_widget,
                             validator = deferred_existing_participant_number_validator,)

_list_alts = [(unicode(x), unicode(x)) for x in range(1, 4)]
_safe_pos_list_alts = [(unicode(x), unicode(x)) for x in range(0, 4)]

@schema_factory('SpeakerListSettingsSchema')
class SpeakerListSettingsSchema(colander.Schema):
    speaker_list_count = colander.SchemaNode(colander.Int(),
                                             title = _(u"Number of speaker lists to use"),
                                             description = _(u"speaker_lists_to_use_description",
                                                             default = u"Using more than one speaker list will prioritise anyone who has spoken less than someone else, "
                                                             u"but only up to number of lists. <br/><br/>"
                                                             u"Example: When using 2 speaker lists, someone who hasn't spoken will get to speak before "
                                                             u"everyone who's spoken 1 or more times. However, when entering the queue someone who's spoken "
                                                             u"2 times and 4 will be treated equally."),
                                             widget = deform.widget.SelectWidget(values = _list_alts),
                                             default = u'1',)
    show_controls_for_participants = colander.SchemaNode(
        colander.Bool(),
        title = _(u"Show user controls for speaker list statuses"),
        description = _(u"show_controls_participants_description",
                        default = u"Users will need participant numbers to add themselves to the speakers list. This includes administrators too!"),
        default = False,
    )
    safe_positions = colander.SchemaNode(
        colander.Int(),
        widget = deform.widget.SelectWidget(values = _safe_pos_list_alts),
        default = u'0',
        title = _(u"Safe positions"),
        description = _(u"safe_positions_description",
                        default = u"Don't move down users from this position even if they should loose their place. "
                            u"For instance, if 1 is entered here and 2 speaker lists are used, the next speaker "
                            u"in line will never be moved down regardless of what list they're on.")
    )
    max_times_in_list = colander.SchemaNode(
        colander.Int(),
        default = 0,
        title = _(u"Maximum times allowed to speak per list"),
        description = _(u"max_times_in_list_description",
                        default = u"If anything else than '0', users aren't able to add themselves to the list when they've "
                        u"spoken more times that this number."))
    reload_manager_interface = colander.SchemaNode(
        colander.Int(),
        default = 4,
        title = _(u"Managers speaker list reload interval"),
        description = _(u"In seconds. After this timeout the list will be updated."),
    )
    reload_speaker_in_queue = colander.SchemaNode(
        colander.Int(),
        default = 5,
        title = _(u"Reload interval for spekers in queue"),
        description = _(u"In seconds. After this timeout the list will be updated."),
    )
    reload_speaker_not_in_queue = colander.SchemaNode(
        colander.Int(),
        default = 15,
        title = _(u"Reload interval for anyone not in queue"),
        description = _(u"In seconds. After this timeout the list will be updated."),
    )


class LogEntries(colander.SequenceSchema):
    log = colander.SchemaNode(colander.Int())


@schema_factory('EditSpeakerLogSchema')
class EditSpeakerLogSchema(colander.Schema):
    logs = LogEntries()

