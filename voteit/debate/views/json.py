# -*- coding: utf-8 -*-
from betahaus.viewcomponent import render_view_group
from betahaus.viewcomponent import view_action
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import MODERATE_MEETING
from voteit.core.security import VIEW
from voteit.irl.plugins.gender import GENDER_NAME_DICT
from voteit.irl.plugins.gender import PRONOUN_NAME_DICT

from voteit.debate.views.base import BaseSLView


@view_defaults(context=IMeeting, renderer='json', permission=NO_PERMISSION_REQUIRED)
class JSONView(BaseSLView):

    def user_resource_data(self, user, pn=None, userid=None, sl=None, is_safe=False, **kw):
        """ Get extra data for a user. Note that the user object might be None.
            This is so we allow these functions to populate default data too."""
        data = dict(
            pn=pn,
            userid=userid,
            active=pn == sl.current,
            listno=self.request.speaker_lists.get_list_number_for(pn, sl),
            is_safe=is_safe,
        )
        data.update(
            # Anything registered within view group 'voteit_debate_userdata' will be added here.
            # So for instance 'fullname' will be included as key, since it's registered below.
            # See betahaus.viewcomponent for more info.
            render_view_group(user, self.request, 'voteit_debate_userdata',
                              view=self, as_type='dict', empty_val='',
                              pn=pn, userid=userid, sl=sl, is_safe=is_safe, **kw)
        )
        return data

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
        for pn in user_pns:
            try:
                pn = int(pn)
            except (ValueError, TypeError):
                pn = None
            userid = n2u.get(pn, '')
            user = None
            if userid:
                user = self.request.root['users'].get(userid, None)
            is_safe = safe_count > user_pns.index(pn)
            list_users.append(
                self.user_resource_data(user, pn=pn, userid=userid, sl=sl, is_safe=is_safe)
            )
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
            active = sl.name in self.all_active_lists
            cat_title = ''
            if active:
                cat = self.request.speaker_lists.get_category_for_list(sl)
                if cat:
                    cat_title = cat.title
            speaker_lists.append({
                'name': sl.name,
                'title': sl.title,
                'active': active,
                'cat_title': cat_title,
                'user_in_list': user_in_list,
                'before_user_count': before_user_count,
                'list_len': len(sl),
                'state': sl.state,
                'state_title': self.request.speaker_lists.get_state_title(sl),
                'user_case': user_case,
            })
        return {'speaker_lists': speaker_lists}


@view_action('voteit_debate_userdata', 'img_url')
def image_url(user, request, va, **kw):
    if user:
        plugin = user.get_image_plugin(request)
        if plugin:
            try:
                img_url = plugin.url(60, request)
            except:
                img_url = None
            if img_url:
                return img_url
    return request.static_url('voteit.debate:static/default_user.png')


@view_action('voteit_debate_userdata', 'gender')
def gender(user, request, va, **kw):
    if user:
        if 'voteit.irl.plugins.gender' in request.registry.settings.get('plugins', ''):
            gender_type = request.speaker_lists.settings.get('show_gender_in_speaker_list', False)
            if gender_type == 'gender':
                return request.localizer.translate(GENDER_NAME_DICT.get(getattr(user, gender_type)))
            elif gender_type == 'pronoun':
                return request.localizer.translate(PRONOUN_NAME_DICT.get(getattr(user, gender_type)))


@view_action('voteit_debate_userdata', 'fullname')
def user_fullname(user, request, va, **kw):
    if user:
        return user.title
    return kw.get('view').no_user_txt


def includeme(config):
    config.scan(__name__)
