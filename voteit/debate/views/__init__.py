# -*- coding: utf-8 -*-

# Constants for slots where you may register extra data to be sent to the speaker lists view templates
USERDATA_SLOT = 'voteit_debate_userdata'  # For manage and fullscreen
CONTEXTLIST_SLOT = 'voteit_debate_contextlist'  # For user controls within the agenda item


def includeme(config):
    config.include('.control_panel')
    config.include('.fullscreen')
    config.include('.json')
    config.include('.log')
    config.include('.manage')
    config.include('.settings')
    config.include('.statistics')
    config.include('.user')
