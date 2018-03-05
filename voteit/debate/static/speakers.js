'use strict';


class SpeakerList {

    constructor() {
        this.load_url = '';
        this.name = null;
        this.queue = [];
        this.current = null;
        this.title = '';
        this.list_users = [];
        this.moderator = false;
        this.start_ts_epoch = null;
        this.directive = {'div.speaker-item': {'speaker<-':{
            //Top node
            '.@class+': function(a) {
                if (a.item.active) return ' active'
            },
            '.@data-speaker-pn': 'speaker.pn',
            // -
            '[data-speaker="listno"]': 'speaker.listno',
            '[data-speaker="pn"]': 'speaker.pn',
            '[data-speaker="fullname"]': 'speaker.fullname',
        }}};
        this.moderator_directive = {};
        this.update_timer = null;
        this.timer_callbacks = [];
        this.update_callbacks = [];
    }

    refresh() {
        var request = arche.do_request(this.load_url);
        request.done(this.handle_response.bind(this));
        return request;
    }

    handle_response(response) {
        this.name = response['name'];
        this.queue = response['queue'];
        this.current = response['current'];
        this.title = response['title'];
        this.state = response['state'];
        this.state_title = response['state_title'];
        this.list_users = response['list_users'];
        this.img_url = response['img_url'];
        if (this.start_ts_epoch != response['start_ts_epoch']) {
            this.start_ts_epoch = response['start_ts_epoch'];
            this.toggle_update_timer();
        }
        this.update_queue();
    }

    toggle_update_timer() {
        if ((!this.update_timer) && (this.start_ts_epoch != null)) {
            console.log('timer started');
            this.update_timer = setInterval(this.handle_timer_ping.bind(this), 100);
        }
        if ((this.update_timer) && (this.start_ts_epoch == null)) {
            console.log('timer stoped');
            clearInterval(this.update_timer);
            this.update_timer = null;
        }
    }

    handle_timer_ping() {
        for (var i = 0, len = this.timer_callbacks.length; i < len; i++) {
            this.timer_callbacks[i](this);
        }
    }

    add_timer_callback(callback) {
        this.timer_callbacks.push(callback);
    }

    add_update_callback(callback) {
        this.update_callbacks.push(callback);
    }

    update_queue() {
        var target = $('[data-speaker-list]');
        target.html($('[data-speaker-template]').html());
        target.render( this.list_users, this.directive );
        for (var i = 0, len = this.update_callbacks.length; i < len; i++) {
            this.update_callbacks[i](this);
        }
    }

    elapsed_time() {
        try {
            //start_ts_epoch is saved in seconds, not miliseconds
            return (new Date).getTime() / 1000 - this.start_ts_epoch;
        } catch(e) {
            return;
        }
    }
}


/* Handles users interaction with the speaker list. */
class UserSpeakerLists {

    constructor() {
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
    }

    refresh() {
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
    }

    timer_refresh() {
        this.update_timer = null;
        this.refresh()
    }

    handle_response(response) {
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
    }

    start_update_timer() {
        this.auto_update = true;
        if (this.update_timer == null) this.refresh()
    }

    stop_update_timer() {
        this.auto_update = false;
    }

    handle_user_action(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var list_name = target.parents('[data-list-name]').data('list-name');
        var action = target.data('sl-user-control');
        var request = arche.do_request(this.action_url, {data: {'action': action, 'sl': list_name}});
        request.done(this.handle_response.bind(this));
    }

}

var speaker_list = new SpeakerList();
var user_speaker_lists = new UserSpeakerLists();


function handle_list_action(event) {
    event.preventDefault();
    var target = $(event.currentTarget);
    var url = target.attr('href');
    var request = arche.do_request(url);
    request.done(function(response) {
         user_speaker_lists.refresh();
    });
}


$(document).ready(function () {
    $('body').on("click", "[data-list-action]", handle_list_action);
    $('body').on("click", "[data-sl-user-control]",
    user_speaker_lists.handle_user_action.bind(user_speaker_lists));
});

/*
function debug_callback(speaker_list) {
    var nowsecs = Math.round((new Date).getTime() / 1000);
    nowsecs - speaker_list.start_ts_epoch
    console.log('timer ping: ', nowsecs - speaker_list.start_ts_epoch);
}
*/

//speaker_list.add_timer_callback(debug_callback);