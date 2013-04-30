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


@schema_factory('SpeakerListSettingsSchema')
class SpeakerListSettingsSchema(colander.Schema):
    speaker_list_count = colander.SchemaNode(colander.Int(),
                                             title = _(u"Number of speaker lists to use"),
                                             description = _(u"speaker_lists_to_use_description",
                                                             default = u""), #FIXME: Go Anders :)
                                             widget = deform.widget.SelectWidget(values = _list_alts),
                                             default = u'1',)
