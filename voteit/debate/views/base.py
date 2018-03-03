from arche.views.base import BaseView
from pyramid.decorator import reify
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
    def context_active(self):
        """ If context is an agenda item,
            is the currently active list ment for that agenda item?
        """
        return self.active_name and self.context.uid in self.active_name

    @reify
    def active_name(self):
        return self.request.speaker_lists.get_active_list()

    @reify
    def participant_numbers(self):
        return IParticipantNumbers(self.request.meeting)

    @reify
    def no_user_txt(self):
        return self.request.localizer.translate(_("(No user registered)"))

    def get_queue_response(self, sl, image=False):
        list_users = []
        n2u = self.participant_numbers.number_to_userid
        user_pns = list(sl)
        if sl.current:
            user_pns.insert(0, sl.current)
        for pn in user_pns:
            try:
                pn = int(pn)
            except (ValueError, TypeError):
                continue
            userid = n2u.get(pn, '')
            img_url = ''
            if userid:
                user = self.request.root['users'].get(userid, None)
                if user:
                    fullname = user.title
                    if image:
                        plugin = user.get_image_plugin(self.request)
                        if plugin:
                            try:
                                img_url = plugin.url(60, self.request)
                            except:
                                pass
            else:
                fullname = self.no_user_txt
            list_users.append(dict(
                pn=pn,
                userid=userid,
                fullname=fullname,
                active=pn == sl.current,
                listno=self.request.speaker_lists.get_list_number_for(pn, sl),
                img_url=img_url,
            ))
        return dict(
            name=sl.name,
            title=sl.title,
            current=sl.current,
            queue=list(sl),
            list_users=list_users,
            start_ts_epoch=sl.start_ts_epoch,
            state=sl.state,
            state_title=self.request.localizer.translate(self.request.speaker_lists.get_state_title(sl))
        )
