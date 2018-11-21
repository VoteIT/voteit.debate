
var FullscreenSpeakers = function() {

    this.load_url = null;
    this.inactive_list_title = 'No list active';

    this.directive = {'div.speaker-item': {'speaker<-':{
        //Top node
        '.@class+': function(a) {
            if (a.item.active) return ' active'
        },
        '[data-speaker="is_safe"]@class+': function(a) {
            if (!a.item.is_safe) return ' hidden'
        },
        '.@data-speaker-pn': 'speaker.pn',
        '[data-speaker="listno"]': 'speaker.listno',
        '[data-speaker="pn"]': 'speaker.pn',
        '[data-speaker="fullname"]': 'speaker.fullname',
        '[data-speaker="gender"]': 'speaker.gender',
        '[data-speaker="img_url"]@src': 'speaker.img_url'

    }}};

    this.update = function() {
        if (!this.load_url) {
            console.log('Load url not set yet, aborting fullscreen update');
            return
        }
        var request = arche.do_request(this.load_url);
        request.done(this.handle_response.bind(this));
        return request;
    }

    this.handle_response = function(response) {
        var response_string = JSON.stringify(response);
        if (this.last_response == response_string) return;
        this.last_response = response_string;
        var target = $('[data-speaker-list]');
        $('[data-list-state]').hide();
        if (response.name != null) {
            target.html($('[data-speaker-template]').html());
            $('[data-list="title"]').html(response.title);
            $('[data-list="state_title"]').html(response.state_title);
            if (response.state == 'open') {
                $('[data-list-state="open"]').show();
            }
            else if (response.state == 'closed')  {
                $('[data-list-state="closed"]').show();
            }
            target.render( response.list_users, this.directive );
        } else {
            target.empty();
            //No active list
            $('[data-list="title"]').html("No active list");

        }
        /*
        for (var i = 0, len = this.update_callbacks.length; i < len; i++) {
            this.update_callbacks[i](this);
        }
        */
    }

    this.init_polling = function() {
        setInterval(this.update.bind(this), 1500);
    }

}


var fullscreen_speakers = new FullscreenSpeakers();
