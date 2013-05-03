from voteit.core.models.interfaces import IJSUtil

from pyramid.i18n import TranslationStringFactory

PROJECTNAME = "voteit.debate"
DebateTSF = TranslationStringFactory(PROJECTNAME)


def includeme(config):
    config.scan()
    from .models import SpeakerListHandler
    config.registry.registerAdapter(SpeakerListHandler)
    
    config.add_translation_dirs('%s:locale/' % PROJECTNAME)

    cache_ttl_seconds = int(config.registry.settings.get('cache_ttl_seconds', 7200))
    config.add_static_view('debate_static', '%s:static' % PROJECTNAME, cache_max_age = cache_ttl_seconds)

    _ = DebateTSF
    js_util = config.registry.getUtility(IJSUtil)
    js_util.add_translations(
        nothing_to_start_error = _(u"Nothing to start"),
        speaker_already_in_list = _(u"Speaker already in this list"),)
