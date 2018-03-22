""" Fanstatic lib"""
from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from fanstatic import Library
from fanstatic import Resource

from voteit.core.fanstaticlib import voteit_main_css
from voteit.core.fanstaticlib import base_js


voteit_debate_lib = Library('voteit_debate_lib', 'static')

voteit_debate_speaker_view_styles = Resource(voteit_debate_lib, 'speaker_view.css', depends=(voteit_main_css,))
voteit_debate_manage_speakers_js = Resource(voteit_debate_lib, 'manage_speakers.js', depends=(base_js,))
voteit_debate_fullscreen_speakers_js = Resource(voteit_debate_lib, 'fullscreen_speakers.js', depends=(base_js,))
voteit_debate_fullscreen_speakers_css = Resource(voteit_debate_lib, 'fullscreen_speakers.css',
                                                 depends=(voteit_main_css, voteit_debate_speaker_view_styles))
voteit_debate_user_speaker_js = Resource(voteit_debate_lib, 'user_speaker.js', depends=(base_js,))
voteit_debate_user_speaker_css = Resource(voteit_debate_lib, 'user_speaker.css')

voteit_debate_gender_statistics_css = Resource(voteit_debate_lib, 'gender_statistics.css', depends=(voteit_main_css,))

def include_user_resources(view, event):
    if view.request.meeting:
        voteit_debate_user_speaker_js.need()
        voteit_debate_user_speaker_css.need()


def includeme(config):
    config.add_subscriber(include_user_resources, [IBaseView, IViewInitializedEvent])
