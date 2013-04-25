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


#@schema_factory('AddSpeakerListSchema')
#class AddSpeakerListSchema(colander.Schema):
#    title = colander.SchemaNode(colander.String(),
#                                title = _(u"Add speaker list"),)
#
#
#@colander.deferred
#def deferred_speaker_list_widget(node, kw):
#    """ Must be used where context contains local selectable lists.
#    """
#    request = kw['request']
#    api = kw['api']
#    sl_handler = request.registry.getAdapter(api.meeting, ISpeakerListHandler)
#    choices = [('', _(u"<Select>"))]
#    for (name, sl) in sl_handler.speaker_lists.items():
#        choices.append((name, sl.title))
#    return deform.widget.SelectWidget(values = choices)
#
#
#@schema_factory('SpeakerListsSchema')
#class SpeakerListsSchema(colander.Schema):
#    list_name = colander.SchemaNode(colander.String(),
#                                    title = _(u"Select list"),
#                                    widget = deferred_speaker_list_widget)
