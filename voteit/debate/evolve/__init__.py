# -*- coding: utf-8 -*-
from arche.models.evolver import BaseEvolver


VERSION = 1


class DebateEvolver(BaseEvolver):
    name = 'voteit.debate'
    sw_version = VERSION
    initial_db_version = 0


def includeme(config):
    config.add_evolver(DebateEvolver)
