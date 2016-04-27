/**
 *javascript web module for kderp_material_price
 * 
 * Mo phong click button search tren form su dung su kien keydown
 * va $.ui.keyCode de lay gia tri cua cac phim dac biet
 * 
 *  
 */

openerp.kderp_material_price = function(instance){
	instance.web.FormView = instance.web.FormView.extend({
		events: {
			'keydown .kderp_material_search_number': function(e){
	            var keys = $.ui.keyCode;
	            switch (e.which) {
	            case keys.ENTER:
					$("button.kderp_material_search_button").click();
				}
			},
			'click td[data-field="pol_detail_show"]>button': 'togglePOLDetails'
		},
		togglePOLDetails: function(e){
			e.preventDefault();
			console.log($(event.target).parents('tr').attr('data-id'));
			$("span.material_price_unique_id input").val($(event.target).parents('tr').attr('data-id'));
			$("button.kderp_material_search_button").click();
			//$('div.kderp_unique_show').toggle(true,'slow');
		},
		load_record: function(record){
			var self = this;
			this._super(record);
			setTimeout(function(){
					if ($("span.material_price_unique_id:last input").val() == "") {
						$("div.kderp_show_unique").hide();
					} else {
						$("div.kderp_show_unique:last").show();
						}				
			},500)
			
		}
	});
	
	instance.kderp_material_price.Hello = instance.web.Widget.extend({
		start: function(){
			console.log("My first widget");
		},
	});
	
	instance.web.client_actions.add('Hello World','instance.kderp_material_price.Hello');
}
