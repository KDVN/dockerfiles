/*---------------------------------------------------------
 * OpenERP replace filters by and condition "and"
 *---------------------------------------------------------*/

openerp.kderp_base = function(instance) {
instance.web.SearchView = instance.web.SearchView.extend(/** @lends instance.web.SearchView# */{
    events: {
    
        'autocompleteopen': function () {
        	console.log(this);
            this.$el.autocomplete('widget').css('z-index', 1004);
        },
    }
    
});
};