import logging
from voteit.core.models.interfaces import IJSUtil

from pyramid.i18n import TranslationStringFactory

PROJECTNAME = "voteit.debate"
DebateTSF = TranslationStringFactory(PROJECTNAME)

log = logging.getLogger(__name__)

def includeme(config):
    config.include('%s.models' % PROJECTNAME)
    config.scan()
    config.add_translation_dirs('%s:locale/' % PROJECTNAME)
    cache_ttl_seconds = int(config.registry.settings.get('cache_ttl_seconds', 7200))
    config.add_static_view('debate_static', '%s:static' % PROJECTNAME, cache_max_age = cache_ttl_seconds)
    _ = DebateTSF
    js_util = config.registry.queryUtility(IJSUtil)
    if js_util:
        #Since this is fine during tests, we're okay with skipping js translations
        js_util.add_translations(
            nothing_to_start_error = _(u"Nothing to start"),
            speaker_already_in_list = _(u"Speaker already in this list"),)
    else:
        log.warn(u"JSUtil not found during startup - ignoring js translations")
