import colander
from betahaus.pyracont.decorators import schema_factory
from voteit.irl.schemas import deferred_autocompleting_participant_number_widget
from voteit.irl.schemas import deferred_existing_participant_number_validator

from . import DebateTSF as _


@schema_factory('AddSpeakerSchema')
class AddSpeakerSchema(colander.Schema):
    pn = colander.SchemaNode(colander.Int(),
                             title = _(u"Add speaker"),
                             widget = deferred_autocompleting_participant_number_widget,
                             validator = deferred_existing_participant_number_validator,)
