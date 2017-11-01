import colander
import deform
from betahaus.pyracont.decorators import schema_factory

from voteit.debate import _
from voteit.debate.models import get_speaker_list_plugins


_list_alts = [(unicode(x), unicode(x)) for x in range(1, 10)]
_safe_pos_list_alts = [(unicode(x), unicode(x)) for x in range(0, 4)]


@colander.deferred
def deferred_speaker_list_plugin_widget(node, kw):
    """ Return a radio choice widget or a hidden widget if it's the default one. """
    request = kw['request']
    values = get_speaker_list_plugins(request)
    if len(values) > 1:
        return deform.widget.RadioChoiceWidget(values = values)
    return deform.widget.HiddenWidget()


class SpeakerListSettingsSchema(colander.Schema):
    enable_voteit_debate = colander.SchemaNode(
        colander.Bool(),
        title = _("Enable speaker lists for this meeting?"),
    )
    speaker_list_count = colander.SchemaNode(
        colander.Int(),
        title = _(u"Number of speaker lists to use"),
        description = _(u"speaker_lists_to_use_description",
                        default = u"Using more than one speaker list will prioritise anyone who "
                        u"has spoken less than someone else, "
                        u"but only up to number of lists. <br/><br/>"
                        u"Example: When using 2 speaker lists, someone who hasn't spoken will "
                        u"get to speak before "
                        u"everyone who's spoken 1 or more times. However, "
                        u"when entering the queue someone who's spoken "
                        u"2 times and 4 will be treated equally."),
        widget = deform.widget.SelectWidget(values = _list_alts),
        default = 9)
    safe_positions = colander.SchemaNode(
        colander.Int(),
        widget = deform.widget.SelectWidget(values = _safe_pos_list_alts),
        default = 1,
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
                        default = u"If anything else than '0', "
                                  u"users aren't able to add themselves to the list when they've "
                        u"spoken more times that this number."))
    reload_manager_interface = colander.SchemaNode(
        colander.Int(),
        default = 4,
        title = _(u"Managers speaker list reload interval"),
        description = _(u"In seconds. After this timeout the list will be updated."),
        tab = 'advanced',
    )
    reload_speaker_in_queue = colander.SchemaNode(
        colander.Int(),
        default = 5,
        title = _(u"Reload interval for spekers in queue"),
        description = _(u"In seconds. After this timeout the list will be updated."),
        tab = 'advanced',
    )
    reload_speaker_not_in_queue = colander.SchemaNode(
        colander.Int(),
        default = 15,
        title = _(u"Reload interval for anyone not in queue"),
        description = _(u"In seconds. After this timeout the list will be updated."),
        tab = 'advanced',
    )
    speaker_list_plugin = colander.SchemaNode(
        colander.String(),
        default = u"",
        title = _(u"Plugin to handle speaker lists"),
        description = _(u"speaker_list_functionality_description",
                        default = u"If you've registered anything esle as a "
                                  u"plugin capable of adjusting speaker list behaviour. "),
        widget = deferred_speaker_list_plugin_widget,
        missing = u"",
        tab = 'advanced')


class LogEntries(colander.SequenceSchema):
    log = colander.SchemaNode(colander.Int())


@schema_factory()
class EditSpeakerLogSchema(colander.Schema):
    logs = LogEntries()


def includeme(config):
    config.add_content_schema('SpeakerLists', SpeakerListSettingsSchema, 'settings')
    config.add_content_schema('SpeakerLists', EditSpeakerLogSchema, 'edit_speaker_log')
