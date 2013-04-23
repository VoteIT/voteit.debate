from voteit.core.models.interfaces import IJSUtil

from pyramid.i18n import TranslationStringFactory

PROJECTNAME = "voteit.debate"
DebateTSF = TranslationStringFactory(PROJECTNAME)


def includeme(config):
    config.scan()
    from .models import SpeakerListHandler
    config.registry.registerAdapter(SpeakerListHandler)

    _ = DebateTSF
    js_util = config.registry.getUtility(IJSUtil)
    js_util.add_translations(
        sort_when_timer_active_error = _(u"Can't sort when timer is running"),
        nothing_to_start_error = _(u"Nothing to start"),
        speaker_already_in_list = _(u"Speaker already in this list"),)
