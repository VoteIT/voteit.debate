var meeting_url = '';
var spoken_time = 0;
var timer = null;

$(document).ready(function () {
    //Load initial data
    meeting_url = $('#meeting_url').attr('href');
    spinner();
    load_speaker_list();
    $('img.spinner').remove();
    
    //Bind events to controls
    $("#start_speaker").on("click", start_speaker);
    $("#pause_speaker").on("click", pause_speaker);
    $("#finished_speaker").on("click", finished_speaker);
    $("#quickstart_next_speaker").on("click", quickstart_next_speaker);
    
    //Add speaker form
    $("form#add_speaker").on("submit", function(event) {
        event.preventDefault();
        spinner().appendTo("input");
        var form = $(this);
        link = form.attr('action');
        $.post(link, form.serialize(), function(data, textStatus, jqXHR) {
            //Handle returned data here
            $('#speaker_queue').append(data);
        })
        .done(function() { 
            $('img.spinner').remove();
            $(".remove_speaker").on("click", remove_speaker);
            //load_speaker_list();
        })
        .fail(function() {
            $('img.spinner').remove();
            flash_message('fubar', 'error', true);
            //flash_message(voteit.translation['permssions_updated_error'], 'error', true); 
        });
    });
    
});

function load_speaker_list() {
    $('#speaker_list').load(meeting_url + '_speaker_listing_moderator', function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message('badness');
        } else {
            //Success
            $(".remove_speaker").on("click", remove_speaker);
        }
    })
}

function remove_speaker(event) {
    event.preventDefault();
    var speaker_to_be_removed = $(this).parents('li');
    var url = $(this).attr('href') + $('#speaker_queue li').index(speaker_to_be_removed);
    spinner().appendTo($(this));
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message('Couldnt remove');
        } else {
            //Success
            $('img.spinner').remove();
            speaker_to_be_removed.remove();
        }
    })
}



function update_timer() {
    spoken_time += 1;
    $('#timer').html(Math.floor(spoken_time / 600) + ':' + Math.floor((spoken_time % 600) / 10) + '.' + (spoken_time % 10));
}

function start_speaker(event) {
    event.preventDefault();
    if ($('#speaker_queue li:first').length == 0) {
        flash_message('Nothing to start');
        return false;
    }
    $('#speaker_queue li:first').addClass('active_speaker');
    $('#speaker_queue li:first .time_spoken').attr('id', 'timer');
    if ($('#timer').html() == '') {
        $('#timer').html('0:0.0');
    }
    var a = $('#timer').html().split(':');
    var b = a[1].split('.')
    spoken_time = parseInt(a[0]) * 600 + parseInt(b[0]) * 10 + parseInt(b[1]);
    if (timer == null) {
        timer = setInterval(update_timer, 100);    
    }
}

function pause_speaker(event) {
    event.preventDefault();
    $('#speaker_queue li:first').removeClass('active_speaker');
    $('#timer').removeAttr('id');
    clearInterval(timer);
    timer = null;
}

function finished_speaker(event) {
    event.preventDefault();
    var speaker_block = $('#speaker_queue li:first');
    $.get(meeting_url + '_speaker_finished?seconds=' + Math.round(spoken_time / 10), function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message('Couldnt go to next');
        } else {
            //Success
            $('img.spinner').remove();
            spoken_time = 0;
            load_speaker_list();
        }
    })
}

function quickstart_next_speaker(event) {
    event.preventDefault();
}
