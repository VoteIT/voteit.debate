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
    }

    refresh() {
        var request = this.load();
        request.done(this.handle_response.bind(this));
    }

    load() {
        var request = arche.do_request(this.load_url);
        request.done(this.handle_response.bind(this))
        return request;
    }

    handle_response(response) {
        this.name = response['name'];
        this.queue = response['queue'];
        this.current = response['current'];
        this.title = response['title'];
        this.list_users = response['list_users'];
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

    update_queue() {
        var target = $('[data-speaker-list]');
        target.html($('[data-speaker-template]').html());
        target.render( this.list_users, this.directive );
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




var speaker_list = new SpeakerList();

/*
function debug_callback(speaker_list) {
    var nowsecs = Math.round((new Date).getTime() / 1000);
    nowsecs - speaker_list.start_ts_epoch
    console.log('timer ping: ', nowsecs - speaker_list.start_ts_epoch);
}
*/

//speaker_list.add_timer_callback(debug_callback);