'use strict';

Vue.component('user-speaker-lists', {
  template: '#speaker-item-tpl',
  data: function() {
    return {
        user_pn: null,
        auto_update: true,
        update_timer: null,
        user_pn: null,
        request_active: false,
        list_data: {},
    };
  },
  props: {
    load_url: {type: String, required: true},
    action_url: {type: String, required: true},
    update_interval: {type: Number, default: 5000},
  },
  mounted: function() {
    this.refresh();
  },
  methods: {
    refresh: function() {
        if (this.request_active) return;
        this.request_active = true
        var request = arche.do_request(this.load_url);
        request.done(this.handle_response);
        request.always(function() {
            this.request_active = false;
            if (this.update_timer == null && this.auto_update == true) {
                this.update_timer = setTimeout(this.timer_refresh.bind(this), this.update_interval);
            }
        }.bind(this))
        return request;
    },
    handle_response: function(response) {
        this.list_data = response;
    },
    timer_refresh: function() {
        this.update_timer = null;
        this.refresh()
    },
    add: function(listName, extraData) {
        this.do_action(listName, 'add', extraData);
    },
    remove: function(listName, extraData) {
        this.do_action(listName, 'remove', extraData);
    },
    do_action: function(listName, action, extraData) {
        var data = {'action': action, 'sl': listName};
        if (extraData !== undefined) $.extend(data, extraData);
        var request = arche.do_request(this.action_url, {data: data})
        request.done(this.handle_response.bind(this))
        request.fail(arche.flash_error)
        return request
    },

    handleExternalAction: function(event) {
        event.preventDefault()
        var target = $(event.currentTarget)
        var url = target.attr('href')
        var request = arche.do_request(url)
        request.done(this.refresh.bind(this))
     }

  }
});
