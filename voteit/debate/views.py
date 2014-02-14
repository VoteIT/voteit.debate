import csv
import StringIO
from decimal import Decimal
from datetime import timedelta

import deform
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.renderers import render
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from betahaus.pyracont.factories import createSchema
from betahaus.viewcomponent import view_action
from voteit.irl.models.interfaces import IParticipantNumbers
from voteit.core.views.base_view import BaseView
from voteit.core.views.meeting import MeetingView
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IMeeting
from voteit.core.schemas.common import add_csrf_token
from voteit.core import security
from voteit.core.fanstaticlib import (voteit_main_css,
                                      jquery_deform)

from .fanstaticlib import voteit_debate_manage_speakers_js
from .fanstaticlib import voteit_debate_speaker_view_styles
from .fanstaticlib import voteit_debate_fullscreen_speakers_js
from .fanstaticlib import voteit_debate_fullscreen_speakers_css
from .fanstaticlib import voteit_debate_user_speaker_js
from .fanstaticlib import voteit_debate_user_speaker_css

from .interfaces import ISpeakerListHandler
from . import DebateTSF as _


class ManageSpeakerList(BaseView):

    @reify
    def sl_handler(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerListHandler)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.api.meeting, IParticipantNumbers)

    @reify
    def active_list(self):
        return self.sl_handler.get_active_list()

    def get_add_form(self):
        schema = createSchema('AddSpeakerSchema')
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        action_url = self.request.resource_url(self.api.meeting, 'speaker_action',
                                               query = {'action': 'add', 'list_name': self.active_list.name})
        return deform.Form(schema, action = action_url, buttons = (deform.Button('add', _(u"Add")),), formid = "add_speaker")

    @view_config(name = "manage_speaker_list", context = IAgendaItem, permission = security.MODERATE_MEETING,
                 renderer = "templates/manage_speaker_list.pt")
    def manage_speaker_list_view(self):
        voteit_debate_manage_speakers_js.need()
        voteit_debate_speaker_view_styles.need()
        if self.active_list:
            self.response['add_form'] = self.get_add_form().render()
        else:
            self.response['add_form'] = u""
        self.response['context_lists'] = self.sl_handler.get_contextual_lists(self.context)
        self.response['context_active'] = self.active_list in self.response['context_lists']
        self.response['active_list'] = self.active_list
        self.response['speaker_item'] = self.speaker_item
        return self.response

    @view_config(name = "speaker_list_action", context = IAgendaItem, permission = security.MODERATE_MEETING)
    def list_action(self):
        #FIXME: This view is up for refactoring.
        action = self.request.GET['action']
        if action == 'add':
            self.sl_handler.add_contextual_list(self.context)
        if action == 'remove':
            name = self.request.GET['name']
            self.sl_handler.remove_list(name)
        if action == 'set':
            name = self.request.GET['name']
            self.sl_handler.set_active_list(name)
        if action == 'clear':
            name = self.request.GET['name']
            self.active_list.speaker_log.clear()
        if action == 'rename':
            name = self.request.GET['name']
            #FIXME: Escape title?
            self.sl_handler.speaker_lists[name].title = self.request.GET['list_title_rename']
            return Response(self.request.GET['list_title_rename'])
        if action == 'set_state':
            name = self.request.GET['name']
            state = self.request.GET['state']
            self.sl_handler.speaker_lists[name].set_state(state)
        if action == 'undo':
            name = self.request.GET['name']
            self.sl_handler.speaker_lists[name].speaker_undo()
        if action == 'shuffle':
            name = self.request.GET['name']
            use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
            self.sl_handler.speaker_lists[name].shuffle(use_lists = use_lists)
        return HTTPFound(location = self.request.resource_url(self.context, "manage_speaker_list"))

    @view_config(name = "speaker_action", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = 'json')
    def speaker_action(self):
        """ Return a json object with status and result.
        
            returned params
            
            success
                True / False

            message
                A string, will be displayed if set
            
            active_speaker
                Rendered html for the active speaker
        
        """
        action = self.request.GET['action']
        #FIXME: This should work on inactive lists too!
        if self.request.GET['list_name'] != self.active_list.name:
            return HTTPForbidden()
        if action == 'active':
            speaker_name = self.request.GET.get('name', None) #Specific speaker, or simply top of the list
            if speaker_name == None:
                if self.active_list.speakers:
                    speaker_name = self.active_list.speakers[0]
                else:
                    return {'success': False, 'message': _(u"No speakers to start")}
            self.active_list.speaker_active(speaker_name)
            return {'success': True, 'active_speaker': self.speaker_item(speaker_name)}
        if action == 'finished':
            seconds = int(self.request.GET['seconds'])
            self.active_list.speaker_finished(seconds)
            return {'success': True}
        if action == 'remove':
            speaker_name = int(self.request.GET['name'])
            self.active_list.remove(speaker_name)
            return {'success': True}
        if action == 'add':
            form = self.get_add_form()
            controls = self.request.POST.items()
            try:
                appstruct = form.validate(controls)
            except deform.ValidationFailure, e:
                #There's only one field with validation. Change otherwise
                return {'success': False, 'message': self.api.translate(e.field['pn'].errormsg)}
            pn = appstruct['pn']
            if pn in self.active_list.speakers:
                #Shouldn't happen since js handles this
                return {'success': False, 'message': _(u"Already in list")}
            if pn in self.participant_numbers.number_to_userid:
                use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
                safe_pos = self.api.meeting.get_field_value('safe_positions', 0)
                self.active_list.add(pn, use_lists = use_lists, safe_pos = safe_pos, override = True)
                return {'success': True}
            else:
                return {'success': False, 'message': _("No user with that number")}
        return {'success': False, 'message': _("Not a valid action")}

    @view_config(name = "_speaker_queue_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_queue_moderator.pt")
    def speaker_queue_moderator(self):
        self.response['active_list'] = self.active_list
        self.response['speaker_item'] = self.speaker_item
        self.response['use_lists'] = self.api.meeting.get_field_value('speaker_list_count', 1)
        self.response['safe_pos'] = self.api.meeting.get_field_value('safe_positions', 0)
        return self.response

    @view_config(name = "_speaker_log_moderator", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/speaker_log_moderator.pt")
    def speaker_log_moderator(self):
        self.response['active_list'] = self.active_list
        number_to_profile_tag = {}
        for pn in self.active_list.speaker_log.keys():
            if pn in self.participant_numbers.number_to_userid:
                userid = self.participant_numbers.number_to_userid[pn]
                number_to_profile_tag[pn] = self.api.get_creators_info([userid], portrait = False)
            else:
                number_to_profile_tag[pn] = pn
        self.response['number_to_profile_tag'] = number_to_profile_tag
        self.response['format_secs'] = self.format_seconds
        return self.response

    def speaker_item(self, pn, use_lists = None, safe_pos = 0):
        if use_lists == None:
            use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
        self.response['pn'] = pn
        userid = self.participant_numbers.number_to_userid.get(int(pn))
        if userid:
            self.response['user_info'] = self.api.get_creators_info([userid], portrait = False)
        else:
            self.response['user_info'] = _(u"(No user associated)")
        self.response['active_list'] = self.active_list
        self.response['use_lists'] = use_lists
        self.response['is_active'] = pn == self.active_list.current
        self.response['is_locked'] = pn in self.active_list.speakers and self.active_list.speakers.index(pn) < safe_pos
        return render("templates/speaker_item.pt", self.response, request = self.request)

    @view_config(name = "edit_speaker_log", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer="voteit.core.views:templates/base_edit.pt")
    def edit_speaker_log(self):
        """ Edit log entries for a specific speaker. """
        speaker_list_name = self.request.GET['speaker_list']
        speaker_list = self.sl_handler.speaker_lists[speaker_list_name]
        speaker = int(self.request.GET['speaker'])
        schema = createSchema("EditSpeakerLogSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context = self.context, request = self.request, api = self.api)
        form = deform.Form(schema, buttons = (deform.Button("save", _(u"Save")), deform.Button("cancel", _(u"Cancel"))))
        post = self.request.POST
        if self.request.method == 'POST':
            if 'save' in post:
                controls = post.items()
                try:
                    appstruct = form.validate(controls)
                except ValidationFailure, e:
                    self.response['form'] = e.render()
                    return self.response
                del speaker_list.speaker_log[speaker][:]
                speaker_list.speaker_log[speaker].extend(appstruct['logs'])
            ai = self.sl_handler.get_expected_context_for(speaker_list.name)
            url = self.request.resource_url(ai, 'manage_speaker_list')
            return HTTPFound(location = url)
        appstruct = {'logs': speaker_list.speaker_log[speaker]}
        self.response['form'] = form.render(appstruct = appstruct)
        return self.response

    def format_seconds(self, secs):
        val = str(timedelta(seconds=int(secs)))
        try:
            return ":".join([x for x in val.split(':') if int(x)])
        except ValueError:
            return val


class SpeakerSettingsView(MeetingView):

    @view_config(context=IMeeting, name="speaker_list_settings", renderer="voteit.core.views:templates/base_edit.pt",
                 permission=security.MODERATE_MEETING)
    def speaker_list_settings(self):
        schema = createSchema("SpeakerListSettingsSchema")
        add_csrf_token(self.context, self.request, schema)
        schema = schema.bind(context=self.context, request=self.request, api = self.api)
        return self.form(schema)


class FullscreenSpeakerList(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(name = "fullscreen_speaker_list", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/fullscreen_view.pt")
    def fullscreen_view(self):
        voteit_main_css.need()
        jquery_deform.need()
        voteit_debate_fullscreen_speakers_js.need()
        voteit_debate_fullscreen_speakers_css.need()
        response = dict()
        return response

    @view_config(name = "_fullscreen_list", context = IMeeting, permission = security.MODERATE_MEETING,
                 renderer = "templates/fullscreen_list.pt")
    def fullscreen_list(self):
        sl_handler = self.request.registry.getAdapter(self.context, ISpeakerListHandler)
        participant_numbers = self.request.registry.getAdapter(self.context, IParticipantNumbers)
        root = self.context.__parent__
        active_list = sl_handler.get_active_list()
        num_lists = self.context.get_field_value('speaker_list_count', 1)
        if active_list.current != None: #Note could be int 0!
            userid = participant_numbers.number_to_userid[active_list.current]
            active_speaker = root.users[userid]
        else:
            active_speaker = None
        speaker_profiles = []
        for num in active_list.speakers:
            userid = participant_numbers.number_to_userid.get(num)
            if userid:
                speaker_profiles.append(root.users[userid])

        def _get_user_list_number(userid):
            num = participant_numbers.userid_to_number[userid]
            spoken_times = len(active_list.speaker_log.get(num, ())) + 1
            return spoken_times <= num_lists and spoken_times or num_lists

        response = dict(
            active_list = active_list,
            active_speaker = active_speaker,
            speaker_profiles = speaker_profiles,
            get_user_list_number = _get_user_list_number,
            userid_to_number = participant_numbers.userid_to_number, #FIXME: This shouldn't be needed, refactor later
        )
        return response


class UserSpeakerLists(BaseView):

    @reify
    def sl_handler(self):
        return self.request.registry.getAdapter(self.api.meeting, ISpeakerListHandler)

    @reify
    def participant_numbers(self):
        return self.request.registry.getAdapter(self.api.meeting, IParticipantNumbers)

    @view_config(name = "_user_speaker_lists", context = IAgendaItem, permission = security.VIEW,
                 renderer = "templates/user_speaker.pt")
    def view(self):
        action = self.request.GET.get('action', None)
        pn = self.participant_numbers.userid_to_number.get(self.api.userid, None)
        use_lists = self.api.meeting.get_field_value('speaker_list_count', 1)
        safe_pos = self.api.meeting.get_field_value('safe_positions', 0)
        max_times_in_list = self.api.meeting.get_field_value('max_times_in_list', 0)
        def _over_limit(sl, pn):
            return max_times_in_list and len(sl.speaker_log.get(pn, ())) >= max_times_in_list
        if pn != None and action:
            list_name = self.request.GET.get('list_name', None)
            if list_name not in self.sl_handler.speaker_lists:
                raise HTTPForbidden(_(u"Speaker list doesn't exist"))
            sl = self.sl_handler.speaker_lists[list_name]
            if action == u'add' and not _over_limit(sl, pn):
                sl.add(pn, use_lists = use_lists, safe_pos = safe_pos)
            if action == u'remove':
                sl.remove(pn)
        self.response['speaker_lists'] = self.sl_handler.get_contextual_lists(self.context)
        self.response['active_list'] = self.sl_handler.get_active_list()
        self.response['pn'] = pn
        self.response['use_lists'] = use_lists
        self.response['safe_pos'] = safe_pos
        self.response['over_limit'] = _over_limit
        self.response['max_times_in_list'] = max_times_in_list
        if pn != None:
            def _show_add(sl, pn):
                return pn != None and sl.state == 'open' and pn not in sl.speakers
            self.response['show_add'] = _show_add
        return self.response

    @view_config(name = "speaker_statistics", context = IMeeting, permission = security.VIEW,
                 renderer = "templates/speaker_statistics.pt")
    def speaker_statistics_view(self):
        self.response['number_to_userid'] = self.participant_numbers.number_to_userid
        #self.response['speaker_lists'] = self.sl_handler.speaker_lists.values()
        results = {}
        maxval = 0
        for sl in self.sl_handler.speaker_lists.values():
            for (pn, entries) in sl.speaker_log.items():
                current = results.setdefault(pn, [])
                current.extend(entries)
                this_val = sum(current)
                if this_val > maxval:
                    maxval = this_val
        self.response['results'] = [(x, results[x]) for x in sorted(results)]

        def _get_percentage(num):
            try:
                return int(round(Decimal(num) / maxval * 100))
            except:
                return u"0%"

        self.response['get_perc'] = _get_percentage
        return self.response

    @view_config(name='speaker_statistics.csv', context=IMeeting, permission=security.VIEW)
    def export(self):
        output = StringIO.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([self.context.title.encode('utf-8')])
        writer.writerow([self.api.translate(_(u"Speaker statistics"))])
        writer.writerow(["#", self.api.translate(_(u"Seconds"))])
        for sl in self.sl_handler.speaker_lists.values():
            if not len(sl.speaker_log):
                continue
            writer.writerow([""])
            writer.writerow([sl.title.encode('utf-8')])
            for (pn, entries) in sl.speaker_log.items():
                for entry in entries:
                    writer.writerow([pn, entry])
        contents = output.getvalue()
        output.close()
        response = Response(content_type='text/csv',
                            body=contents)
        return response


@view_action('meeting', 'fullscreen_speaker_list', title = _(u"Speaker list for projectors"),
             permission = security.MODERATE_MEETING, link = 'fullscreen_speaker_list')
@view_action('meeting', 'speaker_statistics', title = _(u"Speaker statistics"),
             permission = security.VIEW, link = 'speaker_statistics')
@view_action('settings_menu', 'speaker_list_settings', title = _(u"Speaker list settings"),
             permission = security.MODERATE_MEETING, link = 'speaker_list_settings')
def meeting_context_menu_item(context, request, va, **kw):
    api = kw['api']
    url = "%s%s" % (api.meeting_url, va.kwargs['link'])
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('context_actions', 'manage_speaker_list', title = _(u"Manage speaker list"),
             interface = IAgendaItem)
def manage_speaker_list_menu(context, request, va, **kw):
    api = kw['api']
    url = u"%s%s" % (request.resource_url(context), 'manage_speaker_list')
    return """<li><a href="%s">%s</a></li>""" % (url, api.translate(va.title))

@view_action('agenda_item_top', 'user_speaker_list')
def user_speaker_list(context, request, *args, **kw):
    api = kw['api']
    if not api.meeting.get_field_value('show_controls_for_participants', False):
        return u""
    if context.get_workflow_state() not in (u'upcoming', u'ongoing'):
        return u""
    response = dict()
    response.update(kw)
    voteit_debate_user_speaker_js.need()
    voteit_debate_user_speaker_css.need()
    return render("templates/user_speaker_area.pt", response, request = request)
