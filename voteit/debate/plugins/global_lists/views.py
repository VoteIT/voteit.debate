from betahaus.viewcomponent import view_action


@view_action('voteit_debate_userdata', 'time_restriction')
def time_restriction(user, request, va, pn=None, sl=None, **kw):
    """ Add key 'time_restriction' to returned data.
    """
    if request.speaker_lists.name == 'global_lists':
        try:
            return request.speaker_lists.restrictions_active[sl.name][pn]
        except IndexError:
            pass


def includeme(config):
    config.scan(__name__)
