""" Fanstatic lib"""
from arche.fanstatic_lib import pure_js
from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from fanstatic import Library
from fanstatic import Resource
from fanstatic import Group

from voteit.core.fanstaticlib import voteit_main_css
from voteit.core.fanstaticlib import base_js


voteit_debate_lib = Library('voteit_debate_lib', 'static')

main_speaker_css = Resource(voteit_debate_lib, 'css/main.css', depends = (voteit_main_css,))
fullscreen_css = Resource(voteit_debate_lib, 'css/fullscreen.css', depends = (main_speaker_css,))
manage_css = Resource(voteit_debate_lib, 'css/manage.css', depends = (main_speaker_css,))

speakers_js = Resource(voteit_debate_lib, 'speakers.js', depends=(base_js, pure_js))
manage_js = Resource(voteit_debate_lib, 'manage.js', depends = (speakers_js,))
fullscreen_js = Resource(voteit_debate_lib, 'fullscreen.js', depends = (speakers_js,))


#voteit_debate_user_speaker_js = Resource(voteit_debate_lib, 'user_speaker.js', depends = (base_js,))

main_static = Group([main_speaker_css, speakers_js])
fullscreen_static = Group([fullscreen_css, fullscreen_js])
manage_static = Group([manage_css, manage_js])


def include_user_resources(view, event):
    if view.request.meeting:
        #We don't check if it's enabled or anything here.
        main_static.need()


def includeme(config):
    config.add_subscriber(include_user_resources, [IBaseView, IViewInitializedEvent])
