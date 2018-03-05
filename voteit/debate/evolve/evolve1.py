
from voteit.core.models.interfaces import IMeeting
from voteit.debate.interfaces import ISpeakerListSettings


def evolve(root):
    """ Renamed attributes + move values contained in meetings main data storage."""
    _marker = object()
    keys_to_migrate = (
        'speaker_list_plugin',
        'enable_voteit_debate',
        'speaker_list_count',
        'safe_positions',
        'reload_manager_interface',
    )
    keys_to_delete = (
        'max_times_in_list',
        'reload_speaker_in_queue',
        'reload_speaker_not_in_queue',
    )
    for obj in root.values():
        if not IMeeting.providedBy(obj):
            continue
        if hasattr(obj, '__active_speaker_list__'):
            delattr(obj, '__active_speaker_list__')
        if hasattr(obj, '__speaker_lists__'):
            obj._speaker_lists = obj.__speaker_lists__
            delattr(obj, '__speaker_lists__')
        #Simply remove any key with enabled, since we want moderators to revisit this
        obj.field_storage.pop('enable_voteit_debate', None)
        #Store old vals in new adapter
        settings = ISpeakerListSettings(obj)
        for k in keys_to_migrate:
            val = obj.field_storage.pop(k, _marker)
            if val != _marker:
                settings[k] = val
        #Remove keys
        for k in keys_to_delete:
            obj.field_storage.pop(k, None)
        #Add new defaults
        settings['user_update_interval'] = 5
        #The speakers attribute contained the speakers before. It should be labeled data now
        for sl in getattr(obj, '_speaker_lists', {}).values():
            speakers = []
            if hasattr(sl, 'speakers'):
                speakers.extend(sl.speakers)
                delattr(sl, 'speakers')
            sl.data = speakers
