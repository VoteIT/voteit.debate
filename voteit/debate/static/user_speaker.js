var reload_timer = null;


function load_user_speaker_lists() {
    if (reload_timer != null) {
        reload_timer = clearInterval(reload_timer);
    }
    $('#user_speaker_lists').load(user_speaker_list_url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
        } else {
            //Success
        }
        set_reload_timer();
    })
}

$("#user_speaker_lists .sl_controls a").live("click", user_speaker_action);
function user_speaker_action(event) {
    event.preventDefault();
    spinner().appendTo($(event.target));
    if (reload_timer != null) {
        reload_timer = clearInterval(reload_timer);
    }
    var url = $(event.target).attr('href');
    $('#user_speaker_lists').load(url, function(response, status, xhr) {
        if (status == "error") {
            //Sleep, retry
        } else {
            //Success
        }
        set_reload_timer();
        $('img.spinner').remove();
    })
}

function set_reload_timer() {
    if (reload_timer != null) {
        reload_timer = clearInterval(reload_timer);
    }
    var timer_count = 10000;
    if ($('#user_speaker_lists .remove').length > 0) {
        timer_count = 4000;
    }
    reload_timer = setInterval(load_user_speaker_lists, timer_count);    
}
