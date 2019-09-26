import colander
from arche.interfaces import ISchemaCreatedEvent
from pyramid.decorator import reify
from pyramid.threadlocal import get_current_request
from voteit.irl.models.interfaces import IParticipantNumbers
from voteit.irl.plugins.gender import GENDER_NAME_DICT

from voteit.debate import _
from voteit.debate import logger
from voteit.debate.models import SpeakerLists
from voteit.debate.schemas import SpeakerListSettingsSchema


class FemalePriorityLists(SpeakerLists):
    name = "female_priority"
    title = _("Female priority")
    description = _("female_prio_plugin_desc",
                    default="If there are 2 speakers before who aren't females and all "
                            "speakers have spoken the same amount of times, "
                            "the female speaker will be moved up to second position. "
                            "If their are other female speakers in the list, "
                            "the new female speaker will be moved up until she's "
                            "2 positions after any female before her. "
                            "(I.e. pos 3 if pos 1 is female)")
    tpl_manage_speaker_item = 'voteit.debate:plugins/templates/manage_speaker_item_w_gender.pt'

    def get_position(self, pn, sl):
        safe_pos = self.settings.get('safe_positions')
        compare_val = self.get_list_number_for(pn, sl)
        pos = len(sl)
        prio = self.priority_pns(sl, pn)
        for speaker in reversed(sl):
            if pos == safe_pos:
                break
            s_num = self.get_list_number_for(speaker, sl)
            if compare_val > s_num:
                break
            if compare_val == s_num:
                # This is where anyone from a gender that has spoken less gets bumped
                # In that case, break
                if pn not in prio:
                    break
                if speaker in prio:
                    break
                cur_iter_pos = sl.index(speaker)
                if cur_iter_pos > 0:
                    before_pn = sl[cur_iter_pos - 1]
                    if before_pn in prio:
                        break
                else:  # We're at the beginning of the list
                    break
            pos -= 1
        return pos

    def priority_pns(self, sl, *extras):
        prioritized_genders = {'female'}
        if self.settings.get('prioritize_other', False):
            prioritized_genders.add('other')
        results = set()
        pns = list(sl)
        pns.extend(extras)
        for pn in pns:
            userid = self.pns.number_to_userid.get(pn)
            if not userid:
                continue
            user = self.request.root.users.get(userid)
            if user:
                gender = user.get_field_value('gender', None)
                if gender in prioritized_genders:
                    results.add(pn)
        return frozenset(results)

    @reify
    def pns(self):
        return IParticipantNumbers(self.request.meeting)

    def gender_title(self, user):
        gender = getattr(user, 'gender', '')
        return GENDER_NAME_DICT.get(gender, '')


def add_option_to_settings(schema, event):
    request = getattr(event, 'request', get_current_request())
    if request.speaker_lists.name != FemalePriorityLists.name:
        return

    schema.add(
        colander.SchemaNode(
            colander.Bool(),
            title=_("prio_other_too_title",
                    default="Prioritize gender 'other' the same way as females? Applicable only when '${title}' is active.",
                    mapping={'title': request.localizer.translate(FemalePriorityLists.title)}),
            default=False,
            name='prioritize_other',
        )
    )


def includeme(config):
    if 'voteit.irl.plugins.gender' not in config.registry.settings.get('plugins', ''):
        logger.warning("Can't find 'voteit.irl.plugins.gender' in plugins. Adding that package.")
        config.include('voteit.irl.plugins.gender')
    config.registry.registerAdapter(FemalePriorityLists, name=FemalePriorityLists.name)
    config.add_subscriber(add_option_to_settings, [SpeakerListSettingsSchema, ISchemaCreatedEvent])
    assert 'other' in GENDER_NAME_DICT, "Missing 'other' as gender"
