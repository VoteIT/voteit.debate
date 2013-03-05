import colander
from betahaus.pyracont.decorators import schema_factory
from voteit.core.validators import deferred_existing_userid_validator
from voteit.core.schemas.common import deferred_autocompleting_userid_widget

from . import DebateTSF as _


@schema_factory('AddSpeakerSchema')
class AddSpeakerSchema(colander.Schema):
    userid = colander.SchemaNode(colander.String(),
                                 title = _(u"Add speaker"),
                                 widget = deferred_autocompleting_userid_widget,
                                 validator = deferred_existing_userid_validator)
