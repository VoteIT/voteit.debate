'use strict';


var ManageSpeakers = function() {

    this.action_url = null;
    this.auto_update = false;
    this.timer_id = null;
    this.update_interval = 4000;
    this.est_start_ts = null;
    this.speaker_timer = null;

/*
    this.init_sockets = function() {
    }
*/
    this.disable = function() {
        console.log('Disabling');
        this.action_url = null;
        this.auto_update = false;
        if (this.timer_id) clearTimeout(this.timer_id);
        this.timer_id = null;
    }

    this.init_polling = function() {
        console.log('Using polling method');
        this.auto_update = true;
        this.timer_id = setTimeout(this.update.bind(this), this.update_interval);
    }

    //The more old-style hammering of the server...
    this.update = function() {
        if (!this.action_url) {
            console.log('No action url set, aborting update');
            return
        }
        if (this.timer_id) clearTimeout(this.timer_id);
        this.timer_id = null;
        var response = this.send_action({'action': 'refresh'});
        response.always(function(response) {
            if (this.timer_id == null && this.auto_update == true) {
                this.timer_id = setTimeout(function() {
                    this.update();
                }.bind(this), this.update_interval);
            }
        }.bind(this));
    }

    this.handle_response = function(response) {
        var target = $('[data-speaker-list]');
        if (!response.sockets) target.html(response);
    }

    this.send_action = function(data) {
        if (!this.action_url) throw("Action url not set");
        var request = arche.do_request(this.action_url, {data: data});
        request.done(this.handle_response.bind(this));
        request.fail(arche.flash_error);
        return request;
    }

    this.handle_add_pn_submit = function(event) {
        event.preventDefault();
        var form = $(event.currentTarget);
        var speaker_id = $("[name='pn']").val();
        var url = form.attr('action');
        var request = arche.do_request(url, {type: 'POST', data: form.serialize()});
        request.done(function(response) {
            console.log('posted: ', speaker_id);
            $("[name='pn']").val("");
            this.handle_response(response);
        }.bind(this));
        request.fail(function(xhr) {
            $("[name='pn']").parent('.form-group').addClass('has-error');
            $("[name='pn']").focus();
        });
    }

    this.handle_start = function(event) {
        // FIXME: Check att något annat inte är igång?
        event.preventDefault();
        var target = $(event.currentTarget);
        // Is this a play button for a specific speaker, or the generic large one?
        if (target.parents('[data-speaker-pn]').length == 1) {
            var pn = target.parents('[data-speaker-pn]').data('speaker-pn');
        } else {
            var pn = $('[data-speaker-pn]:first').data('speaker-pn');
        }
        if (!pn) return;
        if ($('[data-speaker-active=true]').length > 0) {
            console.log('Speaker already active');
            return
        }
        var data = {'pn': pn, 'action': 'start'};
        var request = this.send_action(data);
        request.done(function(response) {
            console.log('START returned');
            this.est_start_ts = Date.now();
            if (this.speaker_timer) clearInterval(this.speaker_timer);
            this.speaker_timer = setInterval(this.update_spoken_time.bind(this), 100);
        }.bind(this));
    }

    this.handle_finish = function(event) {
        event.preventDefault();
        var data = {'action': 'finish'};
        var request = this.send_action(data);
        request.done(function(response) {
            if (this.speaker_timer) clearInterval(this.speaker_timer);
            $('[data-speaker-time]').empty();
            manage_log.refresh();
        }.bind(this));
    }

    this.handle_undo = function(event) {
        event.preventDefault();
        var data = {'action': 'undo'};
        var request = this.send_action(data);
        request.done(function(response) {
            if (this.speaker_timer) clearInterval(this.speaker_timer);
            $('[data-speaker-time]').empty();
        }.bind(this));
    }

    this.handle_remove = function(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var elem = target.parents('[data-speaker-pn]');
        var pn = elem.data('speaker-pn');
        // FIXME: Ask or don't allow removal of current speaker?
        if (elem.data('speaker-active')) return;
        var data = {'action': 'remove', 'pn': pn};
        this.send_action(data);
    }

    this.handle_shuffle = function(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var data = {'action': 'shuffle'};
        var request = this.send_action(data);
    }

    this.handle_rename = function(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var sl_name = target.data('list-rename-form');
        $('form[data-list-rename-form="' + sl_name + '"]').toggleClass('hidden');
        $('[data-list-rename-title="' + sl_name + '"]').toggleClass('hidden');
    }

    this.update_spoken_time = function() {
        var spoken_time = Date.now() - this.est_start_ts;
        var spoken_time = spoken_time / 1000;
        //Minutes, seconds and tenths
        var st_str = Math.floor(spoken_time / 60) + ':' +
            Math.floor((spoken_time % 60)) + '.' +
            //We care about 10ths
            Math.floor(spoken_time % 1 * 10);
        $('[data-speaker-time]').html(st_str);
    }
}


var ManageLog = function() {

    this.log_url = null;
    this.directive = {'.speaker-log-item': {'speaker<-':{
        '[data-speaker-log="pn"]': 'speaker.pn',
        '[data-speaker-log="fullname"]': 'speaker.fullname',
        '[data-speaker-log="total"]': 'speaker.total',
        '[data-speaker-log="times"]': 'speaker.times',
        '[data-speaker-log="edit"]@href+': function(a) {
            return '&pn=' + a.item.pn;
        }
    }}};


    this.refresh = function() {
        var request = arche.do_request(this.log_url);
        request.done(this.handle_response.bind(this));
    }

    this.handle_response = function(response) {
        var target = $('[data-speaker-log-list]');
        target.html($('[data-speaker-log-template]').html());
        target.render( response, this.directive );
    }
}


var manage_speakers = new ManageSpeakers();
var manage_log = new ManageLog();


$(document).ready(function () {
    //Focus
    $('[name="pn"]').focus();
    $("[name='pn']").on('change', function() {
        $("[name='pn']").parent('.form-group').removeClass('has-error');
    });
    $('body').on("submit", "[data-add-speaker]", manage_speakers.handle_add_pn_submit.bind(manage_speakers));
    $('body').on("click", '[data-list-action="start"]', manage_speakers.handle_start.bind(manage_speakers));
    $('body').on("click", '[data-list-action="undo"]', manage_speakers.handle_undo.bind(manage_speakers));
    $('body').on("click", '[data-list-action="finish"]', manage_speakers.handle_finish.bind(manage_speakers));
    $('body').on("click", '[data-list-action="remove"]', manage_speakers.handle_remove.bind(manage_speakers));
    $('body').on("click", '[data-list-action="shuffle"]', manage_speakers.handle_shuffle.bind(manage_speakers));
    $('body').on("click", '[data-list-action="rename"]', manage_speakers.handle_rename.bind(manage_speakers));
    //speaker_list.add_timer_callback(update_speaker_time);
    //setInterval(speaker_list.refresh.bind(speaker_list), 2000);
});
