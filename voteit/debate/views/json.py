# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config, view_defaults
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW

from voteit.debate.views.base import BaseSLView


@view_defaults(context=IMeeting, renderer='json', permission=NO_PERMISSION_REQUIRED)
class JSONView(BaseSLView):

    @view_config(name='speakers_current_queue.json')
    def speakers_current_queue(self):
        sl = self.request.speaker_lists.get(self.active_name, None)
        if sl is None:
            return {}
        list_users = []
        n2u = self.participant_numbers.number_to_userid
        user_pns = list(sl)
        safe_count = self.request.speaker_lists.settings.get('safe_positions', 1)
        if sl.current:
            user_pns.insert(0, sl.current)
        base_img_url = self.request.static_url('voteit.debate:static/default_user.png')

        def get_gender_display(user):
            pass

        if 'voteit.irl.plugins.gender' in self.request.registry.settings.get('plugins', ''):
            show_gender = self.request.speaker_lists.settings.get('show_gender_in_speaker_list', False)
            if show_gender:
                if show_gender == 'gender':
                    from voteit.irl.plugins.gender import GENDER_NAME_DICT as GENDER_DICT
                elif show_gender == 'pronoun':
                    from voteit.irl.plugins.gender import PRONOUN_NAME_DICT as GENDER_DICT

                def get_gender_display(user):
                    return self.request.localizer.translate(GENDER_DICT.get(getattr(user, show_gender)))

        #total_count = dict([(x, 0) for x in user_pns])
        # if total:
        #     # Calculate total entries for all users.
        #     # FIXME: Should be cached later on
        #     for x in self.request.speaker_lists.values():
        #         for (k, v) in x.speaker_log.items():
        #             if k in user_pns:
        #                 total_count[k] = total_count.get(k, 0) + len(v)
        for pn in user_pns:
            try:
                pn = int(pn)
            except (ValueError, TypeError):
                continue
            userid = n2u.get(pn, '')
            img_url = base_img_url
            fullname = self.no_user_txt
            gender = None
            if userid:
                user = self.request.root['users'].get(userid, None)
                if user:
                    fullname = user.title
                    gender = get_gender_display(user)
                    plugin = user.get_image_plugin(self.request)
                    if plugin:
                        try:
                            img_url = plugin.url(60, self.request)
                        except:
                            pass
            list_users.append(dict(
                pn=pn,
                userid=userid,
                fullname=fullname,
                active=pn == sl.current,
                listno=self.request.speaker_lists.get_list_number_for(pn, sl),
                gender=gender,
                img_url=img_url,
                #total_times_spoken=total_count.get(pn, None),
                is_safe=safe_count > user_pns.index(pn),
            ))
        return dict(
            name=sl.name,
            title=sl.title,
            current=sl.current,
            queue=list(sl),
            list_users=list_users,
            state=sl.state,
            state_title=self.request.speaker_lists.get_state_title(sl)
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
                times=len(entries),
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
                if sl.current == pn:
                    user_case = 'current_speaker'
                else:
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


def includeme(config):
    config.scan(__name__)
