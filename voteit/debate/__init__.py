import logging
from voteit.core.models.interfaces import IJSUtil

from pyramid.i18n import TranslationStringFactory

PROJECTNAME = "voteit.debate"
_ = TranslationStringFactory(PROJECTNAME)

logger = logging.getLogger(__name__)

def includeme(config):
    config.include('.fanstaticlib')
    config.include('.models')
    config.include('.portlet')
    config.include('.schemas')
    config.include('.views')
    config.include('.evolve')
    config.add_translation_dirs('%s:locale/' % PROJECTNAME)
    cache_max_age = int(config.registry.settings.get('arche.cache_max_age', 60*60*24))
    config.add_static_view('debate_static', '%s:static' % PROJECTNAME, cache_max_age = cache_max_age)
    js_util = config.registry.queryUtility(IJSUtil)
    if js_util:
        #Since this is fine during tests, we're okay with skipping js translations
        js_util.add_translations(
            nothing_to_start_error = _(u"Nothing to start"),
            speaker_already_in_list = _(u"Speaker already in this list"),)
    else:
        logger.warn(u"JSUtil not found during startup - ignoring js translations")
