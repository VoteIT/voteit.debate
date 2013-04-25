var timer = null;

$(document).ready(function () {
    load_fullscreen_speaker_list();
});

function load_fullscreen_speaker_list() {
    //spinner().appendTo(('#left'));
    if (timer) {
        timer = clearInterval(timer);
    }
    //console.log('timer unset');
    $('#speaker_list').load('_fullscreen_list', function(response, status, xhr) {
        timer = setInterval(load_fullscreen_speaker_list, 1000);
        //console.log('timer set');
        if (status == "error") {
            $('#status').show();
        } else {
            //Success
        }
    })
};