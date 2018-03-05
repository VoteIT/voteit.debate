# -*- coding: utf-8 -*-
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config, view_defaults
from voteit.core.models.interfaces import IAgendaItem, IMeeting
from voteit.core.security import MODERATE_MEETING, VIEW
from voteit.debate.views.base import BaseSLView
from voteit.debate import _


@view_defaults(context=IMeeting, renderer='json', permission=NO_PERMISSION_REQUIRED)
class JSONView(BaseSLView):

    @view_config(name='speaker_queue.json')
    def queue_view(self, sl_name=None, image=False):
        #Inject category here
        if sl_name is None:
            sl_name = self.request.GET.get('sl', self.request.speaker_lists.get_active_list())
        try:
            sl = self.request.speaker_lists[sl_name]
        except KeyError:
            raise HTTPBadRequest('No such list')
        return self.get_queue_response(sl, image=image)

    @view_config(name='speaker_queue_current.json')
    def queue_current_view(self):
        """ Defaults to current list, and won't accept other options.
            Always returns a translated string appropriate for no active list.
        """
        sl_name = self.request.speaker_lists.get_active_list()
        if sl_name:
            return self.queue_view(sl_name, image=True)
        return dict(
            name="",
            title=self.request.localizer.translate(
                _("No active list")
            ),
        )

    @view_config(name='speaker_log.json', permission=MODERATE_MEETING)
    def log_view(self):
        sl_name = self.request.GET.get('sl', self.request.speaker_lists.get_active_list())
        try:
            sl = self.request.speaker_lists[sl_name]
        except KeyError:
            raise HTTPBadRequest('No such list')
        log_entries = []
        n2u = self.participant_numbers.number_to_userid
        for (pn, entries) in sl.speaker_log.items():
            userid = n2u.get(pn, '')
            if userid:
                fullname = self.request.creators_info(
                    [userid], no_tag=True, no_userid=True, portrait=False
                ).strip()
            else:
                fullname = self.no_user_txt
            log_entries.append(dict(
                pn=pn,
                userid=userid,
                fullname=fullname,
                total=sum(entries),
            ))
        return log_entries

    @view_config(name='context_list_stats.json', context=IAgendaItem, permission=VIEW)
    def context_list_stats_view(self):
        speaker_lists = []
        userid = self.request.authenticated_userid
        pn = None
        if userid:
            pn = self.participant_numbers.userid_to_number.get(userid, None)
        for sl in self.request.speaker_lists.get_lists_in(self.context.uid):
            user_in_list = pn != None and pn in sl
            # Return the users relation to this list expressed as:
            # in_list, not_in_list, no_pn
            before_user_count = None
            if pn is None:
                user_case = 'no_pn'
            elif user_in_list:
                user_case = 'in_list'
                before_user_count = sl.index(pn)
            elif sl.open():
                user_case = 'not_in_list'
            else:
                user_case = 'not_in_list_closed'
            speaker_lists.append({
                'name': sl.name,
                'title': sl.title,
                'active': sl.name == self.active_name,
                'user_in_list': user_in_list,
                'before_user_count': before_user_count,
                'list_len': len(sl),
                'state': sl.state,
                'state_title': self.request.speaker_lists.get_state_title(sl),
                'user_case': user_case,
            })

        return {'speaker_lists': speaker_lists}


    # @view_config(context=IMeeting, name='speaker_data.json')
    # def users_view(self):
    #     results = {}
    #
    #     print self.request.params
    #     n2u = self.participant_numbers.number_to_userid
    #     no_user = self.request.localizer.translate(_("(No user registered)"))
    #     for pn in self.request.params.getall('pn'):
    #         try:
    #             pn = int(pn)
    #         except (ValueError, TypeError):
    #             continue
    #         userid = n2u.get(pn, '')
    #         if userid:
    #             fullname = self.request.creators_info(
    #                 [userid], no_tag=True, no_userid=True, portrait=False
    #             ).strip()
    #         else:
    #             fullname = no_user
    #         results[pn] = dict(
    #             userid = userid,
    #             fullname = fullname
    #         )
    #     print (results)
    #     return results


def includeme(config):
    config.scan(__name__)
