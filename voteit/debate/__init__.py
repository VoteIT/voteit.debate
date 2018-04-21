import logging

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
