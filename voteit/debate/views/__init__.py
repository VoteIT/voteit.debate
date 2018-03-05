# -*- coding: utf-8 -*-


def includeme(config):
    config.include('.control_panel')
    config.include('.fullscreen')
    config.include('.json')
    config.include('.log')
    config.include('.manage')
    config.include('.settings')
    config.include('.statistics')
    config.include('.user')


#FIXME

#More suitable as view code
def get_stats(self, pn, sl, format = True):
    assert isinstance(pn, int)
    assert ISpeakerList.providedBy(sl)
    if pn not in sl.speaker_log:
        return (0, 0)
    time = sum(sl.speaker_log[pn])
    if format:
        time = unicode(timedelta(seconds = time))
    return (len(sl.speaker_log[pn]), time)
