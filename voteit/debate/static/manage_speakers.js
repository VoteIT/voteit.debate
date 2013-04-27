var meeting_url = '';
var spoken_time = 0;
var timer = null;

//Init js code in template!

function load_speaker_queue() {
    spinner().appendTo(('#left'));
    $('#left').load(meeting_url + '_speaker_queue_moderator', function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message(voteit.translation['error_loading'], 'error', true); 
        } else {
            //Success
            $(".promote_start_speaker").on("click", promote_start_speaker);
            $(".remove_speaker").on("click", remove_speaker);
            $("#change_order").on("click", start_change_order);
            $("#save_order").on("click", save_order);
        }
    })
}
function load_speaker_log() {
    spinner().appendTo(('#right'));
    $('#right').load(meeting_url + '_speaker_log_moderator', function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry?
            flash_message(voteit.translation['error_loading'], 'error', true); 
        } else {
            //Success
        }
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
        return false;
    }
    link = form.attr('action');
    $.post(link, form.serialize(), function(data, textStatus, jqXHR) {
        //Handle returned data here
        $('#speaker_queue').append(data);
        $("input[name='pn']").val("");
    })
    .done(function() { 
        $('img.spinner').remove();
        $(".remove_speaker").on("click", remove_speaker);
        //load_speaker_list();
    })
    .fail(function(data) {
        $('img.spinner').remove();
        flash_message(voteit.translation['error_saving'], 'error', true); 
    })
}

function remove_speaker(event) {
    event.preventDefault();
    var speaker_to_be_removed = $(this).parents('li');
    var url = $(this).attr('href');
    spinner().appendTo($(this));
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message(voteit.translation['error_saving'], 'error', true); 
        } else {
            //Success
            $('img.spinner').remove();
            speaker_to_be_removed.remove();
        }
    })
}

function promote_start_speaker(event) {
    event.preventDefault();
    if (timer != null) {
        pause_speaker(event);
    }
    $(this).parents('li').prependTo($(this).parents('ul'))
    save_order(event, start_speaker);
}

function start_change_order(event) {
    event.preventDefault();
    if (timer != null) {
        flash_message(voteit.translation['sort_when_timer_active_error'], 'error', true);
        return false;
    }
    $('#speaker_list_controls').slideUp();
    $("#speaker_queue").sortable();
    $('#save_order').fadeIn();
    
}

function save_order(event, success_callback) {
    event.preventDefault();
    var queue_form = $("form[name=sort_speakers]");
    $.post(queue_form.attr('action'), queue_form.serialize(), function(data, textStatus, jqXHR) {
        //Handle returned data here
    })
    .done(function() {
        // Note callbacks here, we might need to move the other code to it's own call back.
        $('img.spinner').remove();
        $("#speaker_queue").sortable("destroy");
        $('#speaker_list_controls').slideDown();
        $('#save_order').fadeOut();
        if (typeof success_callback !== "undefined") success_callback(event);
    })
    .fail(function() {
        $('img.spinner').remove();
        flash_message(voteit.translation['error_saving'], 'error', true); 
    });
}

function update_timer() {
    spoken_time += 1;
    $('#timer').html(Math.floor(spoken_time / 600) + ':' + Math.floor((spoken_time % 600) / 10) + '.' + (spoken_time % 10));
}

function start_speaker(event) {
    event.preventDefault();

    if ($('#speaker_queue li:first').length == 0) {
        flash_message(voteit.translation['nothing_to_start_error'], 'error', true); 
        return false;
    }
    $('#speaker_queue li:first').addClass('active_speaker');
    $('#speaker_queue li:first .time_spoken').attr('id', 'timer');
    if ($('#timer').html() == '') {
        $('#timer').html('0:0.0');
    }
    spoken_time = parse_spoken_time($('#timer').html());
    if (timer == null) {
        timer = setInterval(update_timer, 100);
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
    $('#speaker_queue li:first').removeClass('active_speaker');
    $('#timer').removeAttr('id');
    clearInterval(timer);
    timer = null;
}

function finished_speaker(event, success_callback) {
    event.preventDefault();
    if (timer != null) {
        pause_speaker(event);
    }
    var speaker_block = $('#speaker_queue li:first');
    spoken_time = parse_spoken_time($('#speaker_queue li:first .time_spoken').html());
    var url = meeting_url;
    url += '_speaker_finished?seconds=' + Math.round(spoken_time / 10);
    url += '&speaker_id=' + speaker_block.children('[name=speaker_id]').attr('value');
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry?
            flash_message(voteit.translation['error_saving'], 'error', true); 
        } else {
            //Success
            $('img.spinner').remove();
            spoken_time = 0;
            speaker_block.remove();
            $('#right').html(response);
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
