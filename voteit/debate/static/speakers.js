'use strict';


/* Handles users interaction with the speaker list. */
var UserSpeakerLists = function() {

    this.load_url = '';
    this.action_url = '';
    this.directive = {'.speaker-list': {'list<-speaker_lists':{
        '[data-user-lists="closed"]@class+': function(a) {
            //Hide this if lists are open
            if (a.list.item.state == 'open') return ' hidden';
        },
        '[data-user-lists="title"]': 'list.title',
        '[data-user-lists="list_len"]': 'list.list_len',
        '.@data-list-name': 'list.name',
        '[data-user-lists="before_user_count"]': 'list.before_user_count',
        '.@class+': function(a) {
            if (a.list.item.active) return ' list-group-item-success';
        }
    }}};
    this.auto_update = false;
    this.update_interval = 5000;
    this.update_timer = null;
    this.update_callbacks = [];
    this.user_pn = null;
    this.request_active = false;
    this.last_response = null;

    this.refresh = function() {
        if (this.request_active) return;
        this.request_active = true
        var request = arche.do_request(this.load_url);
        request.done(this.handle_response.bind(this));
        request.always(function() {
            this.request_active = false;
            if (this.update_timer == null && this.auto_update == true) {
                this.update_timer = setTimeout(this.timer_refresh.bind(this), this.update_interval);
            }
        }.bind(this))
        return request;
    };

    this.timer_refresh = function() {
        this.update_timer = null;
        this.refresh()
    };

    this.handle_response = function(response) {
        var response_string = JSON.stringify(response);
        if (this.last_response == response_string) return;
        var target = $('[data-user-speaker-lists]');
        target.html($('[data-user-speaker-template]').html());
        target.find('[data-user-list-case]').hide();
        target.render( response, this.directive );
        for (var i = 0, len = response.speaker_lists.length; i < len; i++) {
            $('[data-list-name="' + response.speaker_lists[i].name + '"] [data-user-list-case="' + response.speaker_lists[i].user_case + '"]').show();
        }
        for (var i = 0, len = this.update_callbacks.length; i < len; i++) {
            this.update_callbacks[i](this);
        }
        this.last_response = response_string;
    };

    this.start_update_timer = function() {
        this.auto_update = true;
        if (this.update_timer == null) this.refresh()
    };

    this.stop_update_timer = function() {
        this.auto_update = false;
    };

    this.do_request = function(listName, action, extra_data) {
        var data ={'action': action, 'sl': listName};
        if (extra_data !== undefined)
            $.extend(data, extra_data);
        arche.do_request(this.action_url, {data: data})
        .done(this.handle_response.bind(this))
        .fail(arche.flash_error);
    };

    this.handle_user_action = function(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var listName = target.parents('[data-list-name]').data('list-name');
        var action = target.data('sl-user-control');
        // Allow extra data from plugins.
        var extra_data = target.data();
        delete extra_data.slUserControl;
        this.do_request(listName, action, extra_data);
    };
}


function handle_list_action(event) {
    event.preventDefault();
    var target = $(event.currentTarget);
    var url = target.attr('href');
    var request = arche.do_request(url);
    request.done(function(response) {
         user_speaker_lists.refresh();
    });
}


var user_speaker_lists = new UserSpeakerLists();


$(document).ready(function () {
    $('body').on("click", "[data-href-list-action]", handle_list_action);
    $('body').on("click", "[data-sl-user-control]",
    user_speaker_lists.handle_user_action.bind(user_speaker_lists));
});
