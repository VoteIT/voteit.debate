
var meeting_url = '';

$(document).ready(function () {
    //Load initial data
    meeting_url = $('#meeting_url').attr('href');
    spinner();
    load_speaker_list();
    $('img.spinner').remove();
    
    //Add speaker form
    $("form#add_speaker").on("submit", function(event) {
        event.preventDefault();
        spinner().appendTo("input");
        var form = $(this);
        link = form.attr('action');
        $.post(link, form.serialize(), function(data, textStatus, jqXHR) {
            //Handle returned data here
        })
        .done(function() { 
            $('img.spinner').remove();
            load_speaker_list();
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
    var url = $(this).attr('href');
    $('.remove_speaker').attr('href', 'javascript:'); //Disable click
    spinner().appendTo($(this));
    $.get(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message('Couldnt remove');
        } else {
            //Success
            $('img.spinner').remove();
            load_speaker_list();
        }
    })
}
