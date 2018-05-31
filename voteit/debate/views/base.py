from arche.views.base import BaseView
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPBadRequest
from voteit.debate.interfaces import ISpeakerListSettings
from voteit.irl.models.interfaces import IParticipantNumbers

from voteit.debate import _


class BaseSLView(BaseView):
    """ Base view for list things. May be used on any context as long as it's within a meeting.
    """

    @reify
    def settings(self):
        return ISpeakerListSettings(self.request.meeting)

    @reify
    def use_websockets(self):
        return self.settings.get('use_websockets', False)

    @reify
    def context_active(self):
        """ If context is an agenda item,
            is the currently active list ment for that agenda item?
        """
        return self.active_name and self.context.uid in self.active_name

    @reify
    def current_category(self):
        return self.request.GET.get('category', 'default')

    @reify
    def active_name(self):
        return self.request.speaker_lists.get_active_list(self.current_category)

    @reify
    def participant_numbers(self):
        return IParticipantNumbers(self.request.meeting)

    @reify
    def no_user_txt(self):
        return self.request.localizer.translate(_("(No user registered)"))

    @reify
    def sl(self):
        """ Get speaker list from GET/POST 'sl' param. """
        sl_name = self.request.params.get('sl', None)
        try:
            return self.request.speaker_lists[sl_name]
        except KeyError:
            if self.request.registry.settings.get('arche.debug', False):
                raise
            raise HTTPBadRequest(_('No such list'))
