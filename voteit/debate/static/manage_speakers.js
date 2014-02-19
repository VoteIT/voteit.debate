var active_list_action_url = '';
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
});


function load_speaker_queue() {
    if (reload_timer != null) {
        reload_timer = clearInterval(reload_timer);
    }
    return $('#speaker_queue').load(voteit.cfg['meeting_url'] + '_speaker_queue_moderator', function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            $('#status').show();
        } else {
            //Success
            $(".promote_start_speaker").on("click", promote_start_speaker);
            $(".remove_speaker").on("click", remove_speaker);
            $('img.spinner').remove();
        }
        reload_timer = setInterval(load_speaker_queue, reload_interval);
    });
}

function load_speaker_log() {
    if ($('#speaker_log').length > 0) {
        spinner().appendTo('#speaker_log');
        $('#speaker_log').load(voteit.cfg['meeting_url'] + '_speaker_log_moderator', function(response, status, xhr) {
            if (status == "error") {
                //Sleep, retry?
                flash_message(voteit.translation['error_loading'], 'error', true);
            } else {
            }
            $('img.spinner').remove();
        });
    }
}

function load_speaker_lists(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    spinner().appendTo('#reload_slists_js');
    $('#slists').load(url, function(response, status, xhr) {
        if (status == "error") {
            flash_message(voteit.translation['error_loading'], 'error', true, 3, true);
        } else {
            //???
        }
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
    $.get(url, form.serialize(), function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message(voteit.translation['error_saving'], 'error', true);
        } else {
            //Success
            $('#reload_slists_js').click();
        }
    });
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
    link = form.attr('action');
    $.post(link, form.serialize(), function(data, textStatus, jqXHR) {
        if (data['success'] == true) {
            load_speaker_queue();
        }
        if ('message' in data) {
            var msg_cls = data['success'] == true ? 'info' : 'error';
            flash_message(data['message'], msg_cls, true, 5, true);
        }
    })
    .fail(function(jqXHR) {
        flash_message(jqXHR.status + ' ' + jqXHR.statusText, 'error', true, 3, true);
    })
    .always(function() {
        $('img.spinner').remove();
    });
    $("[name='pn']").val("");
}

function remove_speaker(event) {
    event.preventDefault();
    var speaker_to_be_removed = $(this).parents('li');
    var url = $(event.delegateTarget).attr('href');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            flash_message(voteit.translation['error_saving'], 'error', true); 
        } else {
            //Success
            speaker_to_be_removed.remove();
        }
    });
}

function promote_start_speaker(event) {
    //Important, clicked event must be with the same url as start, 
    //but with and added participant numer
    event.preventDefault();
    $.when( $('#finished_speaker').click() ).done( start_speaker(event) );
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
            return $.get(url, function(data, status, xhr) {
                if (status == "error") {
                    //Sleep, retry?
                    flash_message(voteit.translation['error_loading'], 'error', true); 
                    return false;
                } else {
                    //Success
                    $('#speaker_active').html(data['active_speaker']);
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

function finished_speaker(event) {
    event.preventDefault();
    if ($('#speaker_active li').length == 0) {
        return false;
    }
    if (timer != null) {
        pause_speaker(event);
    }
    spoken_time = parse_spoken_time($('#speaker_active li .time_spoken').html());
    var url = $(event.delegateTarget).attr('href');
    url += '&seconds=' + Math.round(spoken_time / 10);
    return $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry?
            flash_message(voteit.translation['error_saving'], 'error', true); 
        } else {
            //Success
            $('img.spinner').remove();
            spoken_time = 0;
            $('#speaker_active li').remove();
            load_speaker_log();
            load_speaker_queue();
        }
    });
}

function quickstart_next_speaker(event) {
    event.preventDefault();
    $.when( $('#finished_speaker').click() )
    .done( $('#start_speaker').click() );
}

function shuffle_speakers(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            flash_message(voteit.translation['error_saving'], 'error', true);
        }
    }).success(load_speaker_queue);
}

function speaker_undo(event) {
    event.preventDefault();
    if (timer != null) {
        pause_speaker(event);
    }
    var url = $(event.delegateTarget).attr('href');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            flash_message(voteit.translation['error_saving'], 'error', true);
        }
    }).success(function() {
        spoken_time = 0;
        $('#speaker_active li').remove();
        load_speaker_queue();
    });
}

function generic_speaker_list_get_actions(event) {
    event.preventDefault();
    var url = $(event.delegateTarget).attr('href');
    if (typeof(url) === 'undefined') return;
    spinner().appendTo(event.target);
    $.get(url, function(data, status, xhr) {
        if (data['success'] == true) {
            $('#reload_slists_js').click();
        }
        if ('message' in data) {
            var msg_cls = data['success'] == true ? 'info' : 'error';
            flash_message(data['message'], msg_cls, true, 5, true);
        }
    }).success(function() {

    }).fail(function(jqXHR) {
        flash_message(jqXHR.status + ' ' + jqXHR.statusText, 'error', true, 3, true);
    }).always(function() {
        $('img.spinner').remove();
    });
}

