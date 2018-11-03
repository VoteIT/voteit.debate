from arche.portlets import get_portlet_manager
from arche.views.base import BaseForm
from arche.views.base import DefaultEditForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config
from voteit.core import security
from voteit.core.models.interfaces import IMeeting

from voteit.debate import _
from voteit.debate.interfaces import ISpeakerListCategories
from voteit.debate.interfaces import ISpeakerListSettings
from voteit.debate.models import SLCategory


@view_config(context=IMeeting,
             name="speaker_list_settings",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class SpeakerListSettingsForm(DefaultEditForm):
    schema_name = 'settings'
    type_name = 'SpeakerLists'
    title = _("Speaker list settings")

    @reify
    def settings(self):
        return ISpeakerListSettings(self.context)

    def appstruct(self):
        return dict(self.settings)

    def save_success(self, appstruct):
        self.settings.update(appstruct)
        self.toggle_portlet(appstruct['enable_voteit_debate'])
        self.flash_messages.add(self.default_success, type="success")
        return HTTPFound(location=self.request.resource_url(self.context))

    def toggle_portlet(self, enable=True):
        manager = get_portlet_manager(self.context)
        current = manager.get_portlets('agenda_item', 'voteit_debate')
        if not enable:
            for portlet in current:
                manager.remove('agenda_item', portlet.uid)
        else:
            if not current:
                new_portlet = manager.add('agenda_item', 'voteit_debate')
                ai_slot = manager['agenda_item']
                current_order = list(ai_slot.keys())
                pos = current_order.index(new_portlet.uid)
                #Find a good position to insert it - above discussions or proposals
                types = ('ai_proposals', 'ai_discussions')
                for portlet in ai_slot.values():
                    if portlet.portlet_type in types:
                        pos = current_order.index(portlet.uid)
                        break
                current_order.remove(new_portlet.uid)
                current_order.insert(pos, new_portlet.uid)
                ai_slot.order = current_order


@view_config(context=IMeeting,
             name="speaker_list_categories",
             renderer="voteit.debate:templates/speaker_list_categories.pt",
             permission=security.MODERATE_MEETING)
class SpeakerListCategorySettingsForm(BaseForm):
    schema_name = 'add_speaker_list_category'
    type_name = 'SpeakerLists'
    title = ""
    appstruct = lambda x: {}

    @reify
    def buttons(self):
        return (self.button_add,)

    @reify
    def categories(self):
        return ISpeakerListCategories(self.context)

    def add_success(self, appstruct):
        category = SLCategory(**appstruct)
        self.categories[category.uid] = category
        self.flash_messages.add(self.default_success, type="success")
        return HTTPFound(location=self.request.resource_url(self.context, 'speaker_list_categories'))


@view_config(context=IMeeting,
             name="edit_speaker_list_category",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class EditSpeakerListCategoryForm(BaseForm):
    schema_name = 'edit_speaker_list_category'
    type_name = 'SpeakerLists'

    @reify
    def title(self):
        return _("Edit '$title'", mapping={'title': self.sl_category.title})

    @reify
    def sl_category(self):
        uid = self.request.GET.get('uid')
        try:
            return self.categories[uid]
        except KeyError:
            raise HTTPNotFound("No such category")

    @reify
    def categories(self):
        return ISpeakerListCategories(self.context)

    def appstruct(self):
        return {
            'title': self.sl_category.title,
            'users': self.sl_category,
        }

    def save_success(self, appstruct):
        self.sl_category.title = appstruct['title']
        if set(self.sl_category) != set(appstruct['users']):
            self.sl_category[:] = appstruct['users']
        reassigned = []
        for cat in self.categories.values():
            if cat is self.sl_category:
                continue
            for userid in appstruct['users']:
                if userid in cat:
                    cat.remove(userid)
                    reassigned.append(userid)
        if reassigned:
            self.flash_messages.add(_("Saved. The following were reassigned: ${names}",
                                      mapping={'names': ", ".join(reassigned)}))
        else:
            self.flash_messages.add(self.default_success, type="success")
        return HTTPFound(location=self.request.resource_url(self.context, 'speaker_list_categories'))


@view_config(context=IMeeting,
             name="remove_speaker_list_category",
             renderer="arche:templates/form.pt",
             permission=security.MODERATE_MEETING)
class RemoveSpeakerListCategoryForm(BaseForm):
    schema_name = 'remove_speaker_list_category'
    type_name = 'SpeakerLists'

    @reify
    def title(self):
        return _("Remove '$title'?", mapping={'title': self.sl_category.title})

    @property
    def buttons(self):
        return (self.button_delete, self.button_cancel)

    @reify
    def sl_category(self):
        uid = self.request.GET.get('uid')
        try:
            return self.categories[uid]
        except KeyError:
            raise HTTPNotFound("No such category")

    @reify
    def categories(self):
        return ISpeakerListCategories(self.context)

    def appstruct(self):
        return {}

    def delete_success(self, appstruct):
        self.request.speaker_lists.del_active_list(self.sl_category.uid)
        del self.categories[self.sl_category.uid]
        self.flash_messages.add(self.default_success)
        return HTTPFound(location=self.request.resource_url(self.context, 'speaker_list_categories'))


def includeme(config):
    config.scan(__name__)
