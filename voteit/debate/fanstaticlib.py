""" Fanstatic lib"""
from fanstatic import Library
from fanstatic import Resource

from voteit.core.fanstaticlib import voteit_main_css
from voteit.core.fanstaticlib import base_js


voteit_debate_lib = Library('voteit_debate_lib', 'static')

voteit_debate_speaker_view_styles = Resource(voteit_debate_lib, 'speaker_view.css', depends = (voteit_main_css,))
voteit_debate_manage_speakers_js = Resource(voteit_debate_lib, 'manage_speakers.js', depends = (base_js,))
voteit_debate_fullscreen_speakers_js = Resource(voteit_debate_lib, 'fullscreen_speakers.js', depends = (base_js,))
voteit_debate_fullscreen_speakers_css = Resource(voteit_debate_lib, 'fullscreen_speakers.css',
                                                 depends = (voteit_main_css, voteit_debate_speaker_view_styles))
voteit_debate_user_speaker_js = Resource(voteit_debate_lib, 'user_speaker.js', depends = (base_js,))
voteit_debate_user_speaker_css = Resource(voteit_debate_lib, 'user_speaker.css')
