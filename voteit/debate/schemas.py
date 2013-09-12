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
                                                             default = u""), #FIXME: Go Anders :)
                                             widget = deform.widget.SelectWidget(values = _list_alts),
                                             default = u'1',)
    show_controls_for_participants = colander.SchemaNode(
        colander.Bool(),
        title = _(u"Show user controls for speaker list statuses"),
        description = _(u"Users will need participant numbers to add themselves to the speakers list. This includes administrators too!"),
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
