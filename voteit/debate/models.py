# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from UserDict import IterableUserDict
from random import shuffle
from uuid import uuid4

from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from arche.utils import AttributeAnnotations
from arche.utils import utcnow
from persistent.list import PersistentList
from pyramid.decorator import reify
from pyramid.interfaces import IRequest
from pyramid.renderers import render
from voteit.core.models.interfaces import IAgendaItem
from voteit.core.models.interfaces import IFlashMessages
from voteit.core.models.interfaces import IMeeting
from zope.component import adapter
from zope.interface import implementer

from voteit.debate import _
from voteit.debate.interfaces import ISLCategory
from voteit.debate.interfaces import ISpeakerList
from voteit.debate.interfaces import ISpeakerListCategories
from voteit.debate.interfaces import ISpeakerListSettings
from voteit.debate.interfaces import ISpeakerLists


@implementer(ISpeakerLists)
@adapter(IMeeting, IRequest)
class SpeakerLists(IterableUserDict, object):
    """ See .interfaces.ISpeakerLists """
    name = ""
    title = _("Default list handler")
    description = ""
    state_titles = {"open": _("Open"), "closed": _("Closed")}
    # See render_tpl
    tpl_manage_speaker_item = 'voteit.debate:templates/snippets/manage_speaker_item.pt'
    tpl_log = 'voteit.debate:templates/snippets/speaker_log_item.pt'
    tpl_fullscreen = 'voteit.debate:templates/snippets/speaker_item_fullscreen.pt'
    tpl_user = 'voteit.debate:templates/snippets/speaker_item_user.pt'

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def data(self):
        # type: () -> OOBTree
        try:
            return self.context._speaker_lists
        except AttributeError:
            self.context._speaker_lists = OOBTree()
            return self.context._speaker_lists

    @reify
    def settings(self):
        schema = self.request.get_schema(self.context, 'SpeakerLists', 'settings')
        settings = dict(ISpeakerListSettings(self.context, SpeakerListSettings(self.context)))
        return self.request.validate_appstruct(schema, settings)

    @reify
    def categories(self):
        return ISpeakerListCategories(self.context)

    @reify
    def user_category(self):
        for cat in self.categories.values():
            if self.request.authenticated_userid in cat:
                return cat.uid
        return 'default'

    @reify
    def category_order(self):
        order = sorted(self.categories.keys(), key=lambda x: self.categories[x].title.lower())
        order.insert(0, 'default')
        return order

    def set_active_list(self, list_name, category=None):
        if category is None:
            category = self.user_category
        if list_name not in self:
            raise KeyError("No list named %r" % list_name)
        try:
            active = self.context._active_lists
        except AttributeError:
            active = self.context._active_lists = OOBTree()
        if active.get(category, object()) == list_name:
            return
        for (other_cat, other_list) in active.items():
            if other_cat == category:
                continue
            if other_list == list_name:
                if other_cat == 'default':
                    title = _("Default")
                    disabled_uid = 'default'
                else:
                    sl_cat = self.categories[other_cat]
                    title = sl_cat.title
                    disabled_uid = sl_cat.uid
                fm = IFlashMessages(self.request)
                msg = _("List was active within '${title}' but was activated here instead.",
                        mapping={'title': title})
                fm.add(msg, type='warning')
                self.del_active_list(disabled_uid)
        active[category] = list_name

    def get_active_list(self, category=None):
        if category is None:
            category = self.user_category
        return self.active_lists.get(category, '')

    def del_active_list(self, category=None):
        if category is None:
            category = self.user_category
        self.active_lists.pop(category, None)

    @property
    def active_lists(self):
        return getattr(self.context, '_active_lists', {})

    def get_category_for_list(self, sl):
        found_category = None
        for (category, name) in self.active_lists.items():
            if sl.name == name:
                found_category = category
                break
        if found_category:
            return self.categories.get(found_category)

    def get_list_names(self, uid):
        results = []
        for name in self:
            if uid in name:
                results.append(name)

        def _sorter(obj):
            try:
                return int(obj.split("/")[1])
            except IndexError:  # pragma: no cover
                return 0  # b/c compat

        return sorted(results, key=_sorter)

    def get_lists_in(self, uid):
        return [self.get(x) for x in self.get_list_names(uid)]

    def add_list_to(self, context):
        assert IAgendaItem.providedBy(context)
        existing = self.get_list_names(context.uid)
        if not existing:
            key = "%s/1" % context.uid
            title = context.title
        else:
            last_list = existing[-1]
            items = last_list.split("/")
            try:
                i = int(items[1]) + 1
            except IndexError:  # pragma: no cover
                i = 1  # b/c compat
            key = "%s/%s" % (context.uid, i)
            title = "%s - %s" % (context.title, i)
        sl = SpeakerList(key, title=title)
        sl.__parent__ = context
        self[key] = sl
        return sl

    def __setitem__(self, key, sl):  # dict api
        if not ISpeakerList.providedBy(sl):
            raise TypeError("Only objects implementing ISpeakerList allowed")  # pragma: no cover
        assert sl.__parent__ is not None
        self.data[key] = sl

    def __delitem__(self, key):  # dict api
        if self.get_active_list() == key:
            self.del_active_list()
        del self.data[key]

    def pop(self, key, *args):
        if self.get_active_list() == key:
            self.del_active_list()
        return self.data.pop(key, *args)

    def __nonzero__(self):
        # Make sure the adapter registers as true even if it's empty
        return True

    def get_state_title(self, sl, translate=True):
        title = self.state_titles.get(sl.state, '')
        if translate:
            return self.request.localizer.translate(title)
        return title

    def add_to_list(self, pn, sl, override=False):
        assert isinstance(pn, int)
        if not override and sl.state == "closed":
            return
        if pn in sl:
            return
        if pn == sl.current:
            return
        sl.chronological.append(pn)
        self.update_order(sl)
        # Done for all in update_order
        return sl.index(pn) + 1

    def finish_on_list(self, sl):
        pn = sl.current
        if pn:
            sl.finish(pn)
            return pn

    def remove_from_list(self, pn, sl):
        if pn in sl:
            sl.remove(pn)
            sl.chronological.remove(pn)
            self.update_order(sl)

    def update_order(self, sl, use_safe=True):
        safe_pos = use_safe and self.settings.get('safe_positions') or 0
        # Touch attribute before delete to make sure any existing lists are copied over
        chronological = sl.chronological
        del sl[safe_pos:]  # Clear list
        for pn in chronological:
            if pn not in sl:
                sl.insert(self.get_position(pn, sl), pn)

    def shuffle(self, sl):
        use_lists = self.settings.get('speaker_list_count')
        lists = {}
        for speaker in sl.chronological:
            cmp_val = len(sl.speaker_log.get(speaker, ())) + 1
            if cmp_val > use_lists:
                cmp_val = use_lists
            cur = lists.setdefault(cmp_val, [])
            cur.append(speaker)
        del sl.chronological[:]
        for i in range(1, use_lists + 1):
            if i in lists:
                shuffle(lists[i])
                sl.chronological.extend(lists[i])
        self.update_order(sl, use_safe=False)

    def get_position(self, pn, sl):
        safe_pos = self.settings.get('safe_positions')
        compare_val = self.get_list_number_for(pn, sl)
        pos = len(sl)
        for speaker in reversed(sl):
            if pos == safe_pos:
                break
            if compare_val >= self.get_list_number_for(speaker, sl):
                break
            pos -= 1
        return pos

    def get_list_number_for(self, pn, sl):
        assert isinstance(pn, int)
        assert ISpeakerList.providedBy(sl)
        use_lists = self.settings.get('speaker_list_count')
        # 1 log entry means secondary speaker list - a val of 2
        cmp_val = len(sl.speaker_log.get(pn, ())) + 1
        return cmp_val <= use_lists and cmp_val or use_lists

    def render_tpl(self, name, **kw):
        tpl = getattr(self, "tpl_%s" % name, None)
        return render(tpl, kw, request=self.request)


@implementer(ISpeakerListSettings)
@adapter(IMeeting)
class SpeakerListSettings(AttributeAnnotations):
    attr_name = '_voteit_debate_settings'


@implementer(ISpeakerListCategories)
@adapter(IMeeting)
class SpeakerListCategories(AttributeAnnotations):
    attr_name = '_voteit_debate_categories'


@implementer(ISpeakerList)
class SpeakerList(PersistentList):
    name = ""
    title = ""
    state = ""
    current = None
    start_ts = None
    __parent__ = None

    def __init__(self, name, title="", state="open"):
        super(SpeakerList, self).__init__()
        self.name = name
        self.speaker_log = IOBTree()
        self.title = title
        self.state = state

    @property
    def chronological(self):
        try:
            return self._chronological
        except AttributeError:
            self._chronological = PersistentList(self)
            return self._chronological

    @property
    def current_secs(self):
        try:
            if self.start_ts is not None:
                ts = utcnow() - self.start_ts
                return ts.seconds
        except AttributeError:  # pragma: no cover
            pass

    def append(self, item):
        self.chronological.append(item)
        super(SpeakerList, self).append(item)

    def extend(self, iterable):
        self.chronological.extend(iterable)
        super(SpeakerList, self).extend(iterable)

    def open(self):
        return self.state == 'open'

    def start(self, pn):
        assert isinstance(pn, int)
        if pn in self:
            self.current = pn
            self.remove(pn)
            self.chronological.remove(pn)
            self.start_ts = utcnow()
            return pn

    def finish(self, pn):
        if self.current != pn:
            return
        assert isinstance(pn, int)
        if self.current not in self.speaker_log:
            self.speaker_log[self.current] = PersistentList()
        self.speaker_log[self.current].append(self.current_secs)
        self.start_ts = None
        self.current = None
        return pn

    def undo(self):
        if self.current is None:
            return
        self.insert(0, self.current)
        self.chronological.insert(0, self.current)
        pn = self.current
        self.current = None
        self.start_ts = None
        return pn

    def __repr__(self):  # pragma : no cover
        return "<%s> '%s' with %s" % (self.__class__.__name__, self.name, super(SpeakerList, self).__repr__())

    def __nonzero__(self):
        return True


@implementer(ISLCategory)
class SLCategory(PersistentList):
    """ Keeps track of moderators who're using a specific list category. """
    title = ""
    uid = ""

    def __init__(self, title="", uid=None):
        super(SLCategory, self).__init__()
        self.title = title
        if uid is None:
            uid = str(uuid4())
        self.uid = uid


def speaker_lists(request, meeting=None):
    """ Will fetch currently set ISpeakerLists adapter.
        Since this will be a cached property on the request object,
        the meeting argument is only for testing.
    """
    if not meeting:
        meeting = request.meeting
    name = ISpeakerListSettings(meeting, {}).get('speaker_list_plugin', '')
    return request.registry.getMultiAdapter([meeting, request], ISpeakerLists,
                                            name=name)


def includeme(config):
    config.add_request_method(speaker_lists, reify=True)
    # The default one won't have a name
    config.registry.registerAdapter(SpeakerLists, name=SpeakerLists.name)
    config.registry.registerAdapter(SpeakerListSettings)
    config.registry.registerAdapter(SpeakerListCategories)
