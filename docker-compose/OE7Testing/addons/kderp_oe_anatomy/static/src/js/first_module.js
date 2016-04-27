//// static/src/js/first_module.js
openerp.kderp_oe_anatomy = function (instance) {
    //instance.web.client_actions.add('example.action', 'instance.kderp_oe_anatomy.action');
    //instance.kderp_oe_anatomy.action = function (parent, action) {
    //    console.log("Executed the action", action);
    //};
	instance.web.client_actions.add('example.action', 'instance.kderp_oe_anatomy.Action');
    instance.kderp_oe_anatomy.Action = instance.web.Widget.extend({
        template: 'kderp_oe_anatomy.action',
        events: {
            'click .oe_kderp_oe_anatomy_start button': 'watch_start',
            'click .oe_kderp_oe_anatomy_stop button': 'watch_stop'
        },
        init: function () {
            this._super.apply(this, arguments);
            this._start = null;
            this._watch = null;
            this.model = new instance.web.Model('kderp_oe_anatomy.stopwatch');
        },
        start: function () {
            var display = this.display_record.bind(this);
            return this.model.query()
                .filter([['user_id', '=', instance.session.uid]])
                .all().done(function (records) {
                    _(records).each(display);
                });
        },
        current: function(){
        	return new Date() - this._start;
            // Subtracting javascript dates returns the difference in milliseconds
        },
        display_record: function (record) {
            $('<li>')
                .text(this.format_time(record.time))
                .appendTo(this.$('.oe_kderp_oe_anatomy_saved'));
        },
        format_time: function (time) {
            var h, m, s;
            s = time / 1000;
            m = Math.floor(s / 60);
            s -= 60*m;
            h = Math.floor(m / 60);
            m -= 60*h;
            return _.str.sprintf("%02d:%02d:%02d", h, m, s);
        },
        update_counter: function (time) {
            this.$('.kderp_oe_anatomy_timer').text(this.format_time(time));
        },
        watch_start: function () {
            this.$el.addClass('oe_kderp_oe_anatomy_started')
                    .removeClass('oe_kderp_oe_anatomy_stopped');
            this._start = new Date();
            // Update the UI to the current time
            this.update_counter(this.current());
            // Update the counter at 30 FPS (33ms/frame)
            this._watch = setInterval(function () {
                this.update_counter(this.current());
            }.bind(this),
                33);
        },
        watch_stop: function () {
            var self=this;
        	clearInterval(this._watch);
            var time = this.current();
            this.update_counter(time);
            this._start = this._watch = null;
        	this.$el.removeClass('oe_kderp_oe_anatomy_started')
                    .addClass('oe_kderp_oe_anatomy_stopped');
            var record = {
                    user_id: instance.session.uid,
                    time: time,
                };
                this.model.call('create', [record]).done(function () {
                    self.display_record(record);
                });
        },
        destroy: function () {
            if (this._watch) {
                clearInterval(this._watch);
            }
            this._super();
        }
    });
};