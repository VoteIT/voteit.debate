
function fullscreen_callback(speaker_list) {
    $('[data-list="title"]').html(speaker_list.title);
    $('[data-list="state_title"]').html(speaker_list.state_title);
    $('[data-list-state]').hide();
    if (speaker_list.state == 'open') {
        $('[data-list-state="open"]').show();
    }
    else if (speaker_list.state == 'closed')  {
        $('[data-list-state="closed"]').show();
    }
}


$(document).ready(function () {
    speaker_list.directive['div.speaker-item']['speaker<-']['[data-speaker="img_url"]@src'] = 'speaker.img_url';
    speaker_list.add_update_callback(fullscreen_callback);
    speaker_list.refresh();
    setInterval(speaker_list.refresh.bind(speaker_list), 1000)
});
