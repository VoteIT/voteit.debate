var timer = null;

$(document).ready(function () {
    load_fullscreen_speaker_list();
});

function load_fullscreen_speaker_list() {
    if (timer) {
        timer = clearInterval(timer);
    }
    $('#speaker_list').load('_fullscreen_list', function(response, status, xhr) {
        timer = setInterval(load_fullscreen_speaker_list, 1000);
        if (status == "error") {
            $('#status').show();
        } else {
            //Success
        }
    })
};
