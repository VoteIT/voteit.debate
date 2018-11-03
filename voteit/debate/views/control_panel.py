from voteit.core import security
from voteit.core.views.control_panel import control_panel_link
from voteit.core.views.control_panel import control_panel_category

from voteit.debate import _
from voteit.debate.interfaces import ISpeakerListSettings


def _debate_is_active(context, request, va):
    return bool(ISpeakerListSettings(request.meeting, {}).get('enable_voteit_debate', None))


def includeme(config):
    config.add_view_action(
        control_panel_category,
        'control_panel', 'debate',
        title=_("Speaker lists"),
        panel_group='debate_control_panel',
        check_active=_debate_is_active
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'settings',
        title=_("Settings"),
        permission=security.MODERATE_MEETING,
        view_name='speaker_list_settings'
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'speaker_list_categories',
        title=_("Multiple lists and categories"),
        view_name='speaker_list_categories'
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'speaker_statistics',
        title=_("Statistics"),
        view_name='speaker_statistics'
    )
    config.add_view_action(
        control_panel_link,
        'debate_control_panel', 'fullscreen_speaker_list',
        title=_("Fullscreen"),
        view_name='fullscreen_speaker_list'
    )
