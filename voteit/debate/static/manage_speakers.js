
$(document).ready(function () {
    //Load initial data
    load_speaker_list();
    
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
            flash_message('Yay!');
            //flash_message(voteit.translation['permssions_updated_success'], 'info', true); 
        })
        .fail(function() {
            $('img.spinner').remove();
            flash_message('fubar');
            //flash_message(voteit.translation['permssions_updated_error'], 'error', true); 
        });
    });
});


function load_speaker_list() {
    $('#speaker_list').load('./_speaker_listing', function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
            flash_message('badness');
        } else {
            //?
        }
    })
}
