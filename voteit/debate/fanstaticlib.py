""" Fanstatic lib"""
from fanstatic import Library
from fanstatic import Resource

from voteit.core.fanstaticlib import voteit_main_css
from voteit.core.fanstaticlib import voteit_common_js

voteit_debate_lib = Library('voteit_debate_lib', 'static')

voteit_debate_speaker_view_styles = Resource(voteit_debate_lib, 'speaker_view.css', depends = (voteit_main_css,))
voteit_debate_manage_speakers_js = Resource(voteit_debate_lib, 'manage_speakers.js', depends = (voteit_common_js,))
