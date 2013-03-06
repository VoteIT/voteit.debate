from pyramid.i18n import TranslationStringFactory

PROJECTNAME = "voteit.debate"
DebateTSF = TranslationStringFactory(PROJECTNAME)


def includeme(config):
    config.scan()
    from .models import SpeakerListHandler
    config.registry.registerAdapter(SpeakerListHandler)
