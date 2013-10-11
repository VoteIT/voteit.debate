var meeting_url = '';
var active_list_action_url = '';
var spoken_time = 0;
var timer = null;
var reload_timer = null;
var reload_interval = 4000;

//Init js code in template!


$(window).on('beforeunload', function() {
    if (($('#speaker_active li .time_spoken').length > 0) && ($('#speaker_active li .time_spoken').html() !== "")) return "Unsaved changes";
});

function load_speaker_queue(success_callback) {
    if (reload_timer != null) {
        reload_timer = clearInterval(reload_timer);
    }
    $('#speaker_queue').load(meeting_url + '_speaker_queue_moderator', function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            $('#status').show();
        } else {
            //Success
            $(".promote_start_speaker").on("click", promote_start_speaker);
            $(".remove_speaker").on("click", remove_speaker);
            $('img.spinner').remove();
            if (typeof success_callback !== "undefined") success_callback(event);
        }
        reload_timer = setInterval(load_speaker_queue, reload_interval);
    })
}

function load_speaker_log() {
    if ($('#speaker_log').length > 0) {
        spinner().appendTo('#speaker_log');
        $('#speaker_log').load(meeting_url + '_speaker_log_moderator', function(response, status, xhr) {
            if (status == "error") {
                //Sleep, retry?
                flash_message(voteit.translation['error_loading'], 'error', true);
            } else {
            }
            $('img.spinner').remove();
        })
    }
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
    $.get(url, form.serialize(), function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message(voteit.translation['error_saving'], 'error', true);
        } else {
            //Success
            // FIXME: This selector is stupid. Watch out!
            form.parents('li').children('.sl_title').show().children('span').html(response);
        }
        $('img.spinner').remove();
        form.hide()
    })
}

function clear_speaker_log(event) {
    event.preventDefault();
    spinner().appendTo($(event.target));
    var url = $(event.target).attr('href');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message(voteit.translation['error_saving'], 'error', true);
        } else {
            //Success
            $("#speaker_log").empty();
        }
        $('img.spinner').remove();
    })
}

function add_speaker(event) {
    event.preventDefault();
    spinner().appendTo("input");
    var form = $(this);
    var speaker_id = $("[name='pn']").attr('value');
    // Does this speaker exist already?
    if ($("#speaker_queue [value='" + speaker_id + "']").length > 0) {
        flash_message(voteit.translation['speaker_already_in_list'], 'error', true);
        $("[name='pn']").val("");
        return false;
    }
    link = form.attr('action');
    $.post(link, form.serialize(), function(data, textStatus, jqXHR) {
        //
    })
    .done(function() { 
        $('img.spinner').remove();
        load_speaker_queue(); //FIXME: Should be returned by view instead
    })
    .fail(function(data) {
        $('img.spinner').remove();
        flash_message(voteit.translation['error_saving'], 'error', true);
    })
    $("[name='pn']").val("");
}

function remove_speaker(event) {
    event.preventDefault();
    var speaker_to_be_removed = $(this).parents('li');
    var url = $(event.delegateTarget).attr('href');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message(voteit.translation['error_saving'], 'error', true); 
        } else {
            //Success
            speaker_to_be_removed.remove();
        }
    })
}

function promote_start_speaker(event) {
    event.preventDefault();
    finished_speaker(event, start_speaker);
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
            var url = active_list_action_url + '&action=active';
            $('#speaker_active').load(url, function(response, status, xhr) {
                if (status == "error") {
                    //Sleep, retry
                    flash_message(voteit.translation['error_loading'], 'error', true); 
                    //flash_message(voteit.translation['nothing_to_start_error'], 'error', true); 
                    return false;
                } else {
                    //Success
                    start_timer();
                    load_speaker_queue();
                }
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

function finished_speaker(event, success_callback) {
    event.preventDefault();
    if ($('#speaker_active li').length == 0) {
        if (typeof success_callback !== "undefined") success_callback(event);
        return false;
    }
    if (timer != null) {
        pause_speaker(event);
    }
    spoken_time = parse_spoken_time($('#speaker_active li .time_spoken').html());
    var url = active_list_action_url;
    url += '&action=finished';
    url += '&seconds=' + Math.round(spoken_time / 10);
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry?
            flash_message(voteit.translation['error_saving'], 'error', true); 
        } else {
            //Success
            $('img.spinner').remove();
            spoken_time = 0;
            $('#speaker_active li').remove();
            $('#speaker_log').html(response);
            load_speaker_queue();
            if (typeof success_callback !== "undefined") success_callback(event);
        }
    })
}

function quickstart_next_speaker(event) {
    event.preventDefault();
    if (timer == null) {
        start_speaker(event);
    } else {
        finished_speaker(event, start_speaker);
    }
}

function shuffle_speakers(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry?
            flash_message(voteit.translation['error_saving'], 'error', true);
        }
    }).success(load_speaker_queue)
}

function speaker_undo(event) {
    event.preventDefault();
    if (timer != null) {
        pause_speaker(event);
    }
    var url = $(event.delegateTarget).attr('href');
    console.log(url);
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry?
            flash_message(voteit.translation['error_saving'], 'error', true);
        }
    }).success(function() {
        spoken_time = 0;
        $('#speaker_active li').remove();
        load_speaker_queue();
    })
}
