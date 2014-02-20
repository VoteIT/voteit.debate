var spoken_time = 0;
var timer = null;
var reload_timer = null;
//reload_interval var is part of init

//Init js code in template!

$(window).on('beforeunload', function() {
    if (($('#speaker_active li .time_spoken').length > 0) && ($('#speaker_active li .time_spoken').html() !== "")) return "Unsaved changes";
});

$(document).ready(function () {
    $("#reload_slists_js").on("click", load_speaker_lists);
    $("#new_speaker_list").on("click", generic_speaker_list_get_actions);
    //Bind events to controls
    $("#start_speaker").on("click", start_speaker);
    $("#pause_speaker").on("click", pause_speaker);
    $("#finished_speaker").on("click", finished_speaker);
    $("#quickstart_next_speaker").on("click", quickstart_next_speaker);
    $("#speaker_undo").on("click", speaker_undo);
    $("#shuffle_speakers").on("click", shuffle_speakers);
    $("form#add_speaker").on("submit", add_speaker);
    $("#clear_speaker_log").on("click", clear_speaker_log);
    //Focus
    $("name=[pn]").focus();
});

function do_request(url, options) {
    var settings = {url: url, async: false};
    if (typeof(options) !== 'undefined') $.extend(settings, options);
    var request = $.ajax(settings);
    request.fail(function(jqXHR) {
        flash_message(jqXHR.status + ' ' + jqXHR.statusText, 'error', true, 3, true);
    });
    request.done(function(data, textStatus, jqXHR) {
        if (typeof(data) === 'object' && 'message' in data) {
            var msg_cls = data['success'] == true ? 'info' : 'error';
            flash_message(data['message'], msg_cls, true, 5, true);
        }
    });
    return request;
}

function load_request(url, target, options) {
    var request = do_request(url, options);
    request.done(function(data) {
        $(target).html(data);
    });
    return request;
}

function load_speaker_queue() {
    if (reload_timer != null) {
        reload_timer = clearInterval(reload_timer);
    }
    var request = load_request(voteit.cfg['meeting_url'] + '_speaker_queue_moderator', '#speaker_queue');
    request.done(function() {
        $(".promote_start_speaker").on("click", promote_start_speaker);
        $(".remove_speaker").on("click", remove_speaker);
        $('img.spinner').remove();
    });
    request.always(function() {
        reload_timer = setInterval(load_speaker_queue, reload_interval);
    });
}

function load_speaker_log() {
    if ($('#speaker_log').length > 0) {
        spinner().appendTo('#speaker_log');
        var request = load_request(voteit.cfg['meeting_url'] + '_speaker_log_moderator', '#speaker_log', {async: true});
        request.always(function() {
            $('img.spinner').remove();
        });
    }
}

function load_speaker_lists(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    spinner().appendTo('#reload_slists_js');
    var request = load_request(url, '#slists');
    request.done(function() {
        $('img.spinner').remove();
        $("#reload_slists_js").on("click", load_speaker_lists);
    });
}

function rename_speaker_show(event) {
    event.preventDefault();
    var sl_item = $(event.target).parents('li');
    sl_item.children('.sl_title').hide();
    sl_item.children('.rename_form').show();
}

function rename_speaker_submit(event) {
    event.preventDefault();
    $(event.target).serialize();
    var form = $(event.target);
    var url = form.attr('action');
    var request = do_request(url, {data: form.serialize()});
    request.done(function() {
        $('#reload_slists_js').click();
    });
}

function clear_speaker_log(event) {
    event.preventDefault();
    spinner().appendTo($(event.target));
    var url = $(event.target).attr('href');
    var request = do_request(url);
    request.done(function() {
        $("#speaker_log").empty();
        $('img.spinner').remove();
    });
}

function add_speaker(event) {
    event.preventDefault();
    spinner().appendTo("input");
    var form = $(this);
    var speaker_id = $("[name='pn']").attr('value');
    // Does this speaker exist already?
    if ($("#speaker_queue [value='" + speaker_id + "']").length > 0) {
        flash_message(voteit.translation['speaker_already_in_list'], 'error', true, 3, true);
        $("[name='pn']").val("");
        return false;
    }
    var url = form.attr('action');
    var request = do_request(url, {type: 'POST', data: form.serialize()});
    request.done(function(data) {
        $("[name='pn']").val("");
        load_speaker_queue();
    });
    request.always(function() {
        $('img.spinner').remove();
    });
}

function remove_speaker(event) {
    event.preventDefault();
    var speaker_to_be_removed = $(this).parents('li');
    var url = $(event.delegateTarget).attr('href');
    var request = do_request(url);
    request.done(function(){
        speaker_to_be_removed.remove();
        load_speaker_queue();
    });
}

function promote_start_speaker(event) {
    //Important, clicked event must be with the same url as start, 
    //but with and added participant numer
    event.preventDefault();
    finished_speaker(event, false);
    start_speaker(event);
}

function update_timer() {
    spoken_time += 1;
    $('#timer').html(Math.floor(spoken_time / 600) + ':' + Math.floor((spoken_time % 600) / 10) + '.' + (spoken_time % 10));
}

function start_timer() {
    $('#speaker_active li .time_spoken').attr('id', 'timer');
    if ($('#timer').html() == '') {
        $('#timer').html('0:0.0');
    }
    spoken_time = parse_spoken_time($('#timer').html());
    if (timer == null) {
        timer = setInterval(update_timer, 100);
    }
}

function start_speaker(event) {
    event.preventDefault();
    if ($('#speaker_active li').length == 0) {
        if ($('#speaker_queue li').length != 0) {
            var url = $(event.delegateTarget).attr('href');
            var request = do_request(url);
            request.done(function(data) {
                $('#speaker_active').html(data['active_speaker']);
                start_timer();
                load_speaker_queue();
            });
        }
    } else {
        start_timer();
    }

}

function parse_spoken_time(text) {
    // Parse a string like "10:11.7", with 10 as minutes, 11 as seconds and 7 as tenths of a second.
    if (!text) return 0;
    var a = text.split(':');
    var b = a[1].split('.');
    return parseInt(a[0]) * 600 + parseInt(b[0]) * 10 + parseInt(b[1]);
}

function pause_speaker(event) {
    event.preventDefault();
    $('#timer').removeAttr('id');
    clearInterval(timer);
    timer = null;
}

function finished_speaker(event, reload_queue) {
    var reload_queue = typeof(reload_queue) === 'undefined' ? true : reload_queue;
    event.preventDefault();
    if ($('#speaker_active li').length == 0) {
        return false;
    }
    if (timer != null) {
        pause_speaker(event);
    }
    spoken_time = parse_spoken_time($('#speaker_active li .time_spoken').html());
    var url = $("#finished_speaker").attr('href');
    url += '&seconds=' + Math.round(spoken_time / 10);
    //var request = $.ajax({url: url, async: false});
    var request = do_request(url);
    request.done(function() {
        //Success
        $('img.spinner').remove();
        spoken_time = 0;
        $('#speaker_active li').remove();
        load_speaker_log();
        if (reload_queue) {
            //This might mess up other deferred events
            load_speaker_queue();
        }
    });
}

function quickstart_next_speaker(event) {
    event.preventDefault();
    finished_speaker(event, false);
    $('#start_speaker').click();
}

function shuffle_speakers(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    var request = do_request(url);
    request.done(load_speaker_queue);
}

function speaker_undo(event) {
    event.preventDefault();
    if (timer != null) {
        pause_speaker(event);
    }
    var url = $(event.delegateTarget).attr('href');
    var request = do_request(url);
    request.done(function() {
        spoken_time = 0;
        load_speaker_queue();
        $('#speaker_active li').remove();
    });
}

function generic_speaker_list_get_actions(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    if (typeof(url) === 'undefined') return;
    spinner().appendTo(event.target);
    var request = do_request(url);
    request.done(function(data) {
        if (data['success'] == true) {
            $('#reload_slists_js').click();
            //Spinner cleared by this action
        }
    });
}
