from pyramid.traversal import find_interface
from pyramid.threadlocal import get_current_request
from voteit.core.models.interfaces import IMeeting
from voteit.irl.models.interfaces import IParticipantNumbers

#from voteit.debate.models import SpeakerListPlugin
from voteit.debate import _
from voteit.debate import logger


def pn_to_gender_dict(context, request = None):
    if request is None:
        request = get_current_request()
    meeting = find_interface(context, IMeeting)
    participant_numbers = request.registry.getAdapter(meeting, IParticipantNumbers)
    root = meeting.__parent__
    results = {}
    for (pn, userid) in participant_numbers.number_to_userid.items():
        gender = root.users[userid].get_field_value('gender', None)
        if gender:
            results[pn] = gender
    return results

def female_pns(context, request, *args):
    if request is None:
        request = get_current_request()
    meeting = find_interface(context, IMeeting)
    root = meeting.__parent__
    participant_numbers = request.registry.getAdapter(meeting, IParticipantNumbers)
    results = set()
    for pn in args:
        userid = participant_numbers.number_to_userid.get(pn)
        if not userid:
            continue
        user = root.users.get(userid)
        if user:
            gender = user.get_field_value('gender', None)
            if gender == 'female':
                results.add(pn)
    return frozenset(results)


# class FemalePrioritySL(SpeakerListPlugin):
#     """ Females bypass any other gender if they're on the same list, and the
#         speaker before isn't a female.
#     """
#     plugin_name = u'female_priority'
#     plugin_title = _("female_prio_plugin_title",
#                      default = u"Females get to be moved up")
#     plugin_description = _(u"female_prio_plugin_desc",
#                            default=u"If there are 2 speakers before who aren't females and all "
#                            u"speakers have spoken the same amount of times, "
#                            u"the female speaker will be moved up to second position. "
#                            u"If their are other female speakers in the list, "
#                            u"the new female speaker will be moved up until she's "
#                            u"2 positions after any female before her. "
#                            u"(I.e. pos 3 if pos 1 is female)")
#
#     def get_position(self, pn):
#         #See tests for this function :)
#         #use_lists = self.settings.get('speaker_list_count')
#         safe_pos = self.settings.get('safe_positions')
#         compare_val = self.get_number_for(pn)
#         pos = len(self.speakers)
#         females = female_pns(self, None, pn, *self.speakers)
#         for speaker in reversed(self.speakers):
#             if pos == safe_pos:
#                 break
#             s_num = self.get_number_for(speaker)
#             if compare_val > s_num:
#                 break
#             if compare_val == s_num:
#                 #This is where anyone from a gender that has spoken less gets bumped
#                 #In that case, break
#                 if pn not in females:
#                     break
#                 if speaker in females:
#                     break
#                 cur_iter_pos = self.speakers.index(speaker)
#                 if cur_iter_pos > 0:
#                     before_pn = self.speakers[cur_iter_pos-1]
#                     if before_pn in females:
#                         break
#             pos -= 1
#         return pos


def includeme(config):
    if 'voteit.irl.plugins.gender' not in config.registry.settings.get('plugins', ''):
        logger.warning("Can't find 'voteit.irl.plugins.gender' in plugins. Adding that package.")
        config.include('voteit.irl.plugins.gender')
    #config.registry.registerAdapter(FemalePrioritySL, name = FemalePrioritySL.plugin_name)
