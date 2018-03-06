'use strict';


class ManageSpeakers {

    constructor() {
        this.action_url = null;
    }

    handle_add_pn_submit(event) {
        event.preventDefault();
        var form = $(event.currentTarget);
        var speaker_id = $("[name='pn']").val();
        var url = form.attr('action');
        var request = arche.do_request(url, {type: 'POST', data: form.serialize()});
        request.done(function(response) {
            console.log('posted: ', speaker_id);
            $("[name='pn']").val("");
//            speaker_list.handle_response(response);
            speaker_list.refresh();

        });
        request.fail(function(xhr) {
            $("[name='pn']").parent('.form-group').addClass('has-error');
            $("[name='pn']").focus();
        });
    }

    handle_start(event) {
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
        var data = {'pn': pn, 'action': 'start'};
        var request = arche.do_request(this.action_url, {data: data});
        request.done(function(response) {
            speaker_list.refresh();
            //speaker_list.handle_response(response);
        }.bind(this));
        request.fail(arche.flash_error);
    }

    handle_finish(event) {
        event.preventDefault();
        if (!speaker_list.current) {
            speaker_list.refresh();
            return
        }
        var data = {'pn': speaker_list.current, 'action': 'finish'};
        var request = arche.do_request(this.action_url, {data: data});
        request.done(function(response) {
            $('[data-speaker-time]').empty();
            speaker_list.refresh();
            //speaker_list.handle_response(response);
            manage_log.refresh();
        }.bind(this));
        request.fail(arche.flash_error);
    }

    handle_undo(event) {
        event.preventDefault();
        var data = {'action': 'undo'};
        var request = arche.do_request(this.action_url, {data: data});
        request.done(function(response) {
            speaker_list.refresh();
            //speaker_list.handle_response(response);
            $('[data-speaker-time]').empty();
        }.bind(this));
        request.fail(arche.flash_error);
    }

    handle_remove(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var pn = target.parents('[data-speaker-pn]').data('speaker-pn');
        // FIXME: Ask or don't allow removal of current speaker
        if (pn == speaker_list.current) return;
        var data = {'action': 'remove', 'pn': pn};
        var request = arche.do_request(this.action_url, {data: data});
        request.done(function(response) {
            speaker_list.refresh();
            //speaker_list.handle_response(response);
        }.bind(this));
        request.fail(arche.flash_error);
    }

    handle_shuffle(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var data = {'action': 'shuffle'};
        var request = arche.do_request(this.action_url, {data: data});
        request.done(function(response) {
            speaker_list.refresh();
            //speaker_list.handle_response(response);
        }.bind(this));
        request.fail(arche.flash_error);
    }

    handle_rename(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var sl_name = target.data('list-rename-form');
        $('form[data-list-rename-form="' + sl_name + '"]').toggleClass('hidden');
        $('[data-list-rename-title="' + sl_name + '"]').toggleClass('hidden');
    }
}


class ManageLog {
    constructor() {
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
    }

    refresh() {
        var request = arche.do_request(this.log_url);
        request.done(this.handle_response.bind(this));
    }

    handle_response(response) {
        var target = $('[data-speaker-log-list]');
        target.html($('[data-speaker-log-template]').html());
        target.render( response, this.directive );
    }
}


var manage_speakers = new ManageSpeakers();
var manage_log = new ManageLog();


function update_speaker_time(speaker_list) {
    var spoken_time = speaker_list.elapsed_time()
    //Minutes, seconds and tenths
    var st_str = Math.floor(spoken_time / 60) + ':' +
        Math.floor((spoken_time % 60)) + '.' +
        Math.floor(spoken_time % 1 * 10);
    $('[data-speaker-time]').html(st_str);
}

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
    speaker_list.add_timer_callback(update_speaker_time);
    setInterval(speaker_list.refresh.bind(speaker_list), 2000);
});
