//For Learning
//on_menu_settings: function() {
//    var self = this;
//    if (!this.getParent().has_uncommitted_changes()) {
//        self.rpc("/web/action/load", { action_id: "base.action_res_users_my" }).done(function(result) {
//            result.res_id = instance.session.uid;
//            self.getParent().action_manager.do_action(result);
//        });
//    }
//},
openerp.kderp_web = function(session) {
    var _t = session.web._t;
    var QWeb = session.web.qweb;
    var has_action_id = false;
    var editmode_attachement=false;
    var unlinkable=false;
    var _lt = session.web._lt;
    //For Sort field in sidebar
    var vsort_by_field_att='label';
    //For string in Search
    var less_than_str = _t("Less Than ");
    var greater_than_str = _t("Greater Than ");

    session.web.form.widgets.add('many2oneimage','session.web.form.FieldMany2OneImage');

    //Change link favicon
    $('link[href="/web/static/src/img/favicon.ico"]').attr('href','/kderp_web/static/src/img/favicon.ico');
    (function() {
        var link = document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = 'shortcut icon';
        link.href = '/kderp_web/static/src/img/favicon.ico';
        document.getElementsByTagName('head')[0].appendChild(link);
    }());

    //Move to Top Page
    var move_top_page = function (move)
    		{
    			move = typeof move !== 'undefined' ? move : true;
    			//Check top or not
    			if (move)
    				{
	    			var $win = $(window);
	    			if ($win.scrollTop() == 0)
	    				move=false;
    				}

    			if (move)
    				return $("html, body").animate({ scrollTop: 0},"fast")
    		};

//Function Attach Input mask
	var attach_mask_editable= function (obj,record) {
    			var normalize_format = function (format) {
    			    return Date.normalizeFormat(session.web.strip_raw_chars(format));
    			};
    			var l10n = _t.database.parameters;
    			var date_pattern = normalize_format(_t.database.parameters.date_format);

    			var excepted_list_fields=['due_date2'];

    			$.extend($.inputmask.defaults, {
    			    'clearMaskOnLostFocus': true
    			});
    			//Them Input Mask Pattern)
    			$.extend($.inputmask.defaults.aliases, {
    			'dd-mm-yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MM-yyyy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MMM-yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MM-yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MMM-yyyy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd/mm/yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd/mm/yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    }});

    			obj.each( function( index, element ){
    				var main_elem=$( this );
    				elem=main_elem[0];

    				if (excepted_list_fields.indexOf(elem.name)<0)
    					{
    					if ( (typeof(elem.classList) !== 'undefined'))
    						if (elem.classList.contains('oe_datepicker_master') || check_parent(elem,'oe_datepicker_master'))
    								{
    								if (typeof(elem.value) !== 'undefined' && elem.value !== null && elem.value !== "")
    									{
    										try
    											{
    											get_date=elem.value;
    											if (typeof(record)==='object')
    												{
    													get_date=record[elem.name];
    													var date = Date.parseExact(get_date, 'yyyy-MM-dd');
    												}
    											else
    												var date = Date.parseExact(get_date, date_pattern);

    											if (date===null && typeof(elem.value)==='string')
    												date_value=elem.value;
    											else
    												date_value=date.toString(normalize_format(l10n.date_format).replace("MMM","M"));

    											elem.value=date_value;
    											}
    										catch (err)
    											{
    											console.log(elem.value);
    											console.log(date);
    											console.log(date_pattern);
    											console.log(elem.value);
    											}

    									}
    								input_mask=normalize_format(l10n.date_format).replace("MMM","mm");
    								main_elem.inputmask(input_mask);

    								main_elem.bind({
    									focusout :function() {
    									  	check_and_complete_date(this,input_mask,date_pattern);
    								  	},
    									hover: function() {
    									  	check_and_complete_date(this,input_mask,date_pattern);
    									  	},
//    									  blur: function() {
//    										  	check_and_complete_date(this,input_mask,date_pattern);
//    										  	},
    									});
    							}
    						else
    							if (check_parent(elem,'oe_form_field_float'))
    								{
    									if (check_parent(elem,'spinner'))
    										{

    										$( elem).spinner();
    										$(elem).addClass('oe_form_field_float');
    										main_elem.inputmask('decimal', { rightAlignNumerics: false, groupSeparator: ',', autoGroup: true });
    										}
    									else
    										main_elem.inputmask('decimal', { rightAlignNumerics: false, groupSeparator: ',', autoGroup: true });
    								}
    					}

    			});
    		};

//    var old_func=session.web.fields_view_get;
//    session.web.fields_view_get = function (args) {
//    	console.log(args);
//    	console.log("ARGS");
//    	return old_func(args);
//    };

    session.web.DataSetSearch = session.web.DataSetSearch.extend({
    	read_slice: function (fields, options) {
    		var _super=this._super(fields,options);
    		return $.when(_super,move_top_page($(".ui-dialog-content").length<=0));
    	}
    });
    //End of Move to Top Page

    /* Extend the Sidebar to add Share and Embed links in the 'More' menu */
    session.web.Sidebar.include({
    	sort_sidebar: function () {
    		var obj=this;
    		var vsort_by_field='label';
            var sort_by = function(field, reverse, primer){
            	   var key = primer ?
            	       function(x) {return primer(x[field])}:
            	       function(x) {return x[field]};

            	   reverse = [-1, 1][+!!reverse];

            	   return function (a, b) {

            	       return a = key(a), b = key(b), reverse * ((a > b) - (b > a));
            	     }
            	};

            for (section_code in obj.items)
            	{
	            	if (section_code==='other')
	            		{
		            		obj.items[section_code].forEach(function (value)
		            				{
		            				special_char=String.fromCharCode(255);
		            				if (value.label==='Duplicate')
		            					value.sort_label=special_char+'00';
		            				else if (value.label==='Delete')
		            					value.sort_label=special_char+'05';
		            				else if (value.label==='Export')
		            					value.sort_label=special_char+'10';
		            				else if (value.label==='View Log')
		            					value.sort_label=special_char+'15';
		            				else
		            					value.sort_label=value.label;
		            				});
		            	obj.items[section_code].sort(sort_by('sort_label', true, function(a){return a.toUpperCase()}));
	            		}
	            	else if (section_code==='files')
	            		{
        				obj.items[section_code].sort(sort_by(vsort_by_field_att, true, function(a){return a;}));
	            		}
	            	else
	            		{
	            		obj.items[section_code].sort(sort_by(vsort_by_field, true, function(a){return a.toUpperCase()}));
	            		}
            	}
        },

    	redraw: function() {
            var _super=this._super(this);
            var self =this;
            return $.when(_super).done(self.sort_sidebar());
        },

        on_attachments_loaded: function(attachments) {
		      var self = this;
		      var _super=self._super(attachments);
		      return $.when(this._super(attachments)).done(self.sort_sidebar());
        	},

    });

    //Hide Delete Attachment in some Model
    session.web.Sidebar = session.web.Sidebar.extend({

        start: function() {
        	new session.web.Model("ir.attachment").get_func("has_gorup_hidden")(session.uid).pipe(function(result) {
        		editmode_attachement=result;});

        	new session.web.Model("ir.attachment").get_func("check_location")(session.uid).pipe(function(result) {
    			if (result!=='hcm')
    				{
    				vsort_by_field_att='create_date';
    				}
    			else
    				vsort_by_field_att='label';
    			});

            var self = this;
            var _super=this._super(this);
            this.exept_model=['sale.order','purchase.order','account.invoice','kderp.contract.client'];
            this.editmode_attachement=editmode_attachement;

            self.add_items('other', [
                {   label: _t('View Log'),
                    callback: self.on_click_view_log,
                    classname: 'oe_share' },
            ]);
            return _super;
        },

        on_click_view_log: function(item) {
        	self=this;
            var view = this.getParent();
            this.dataset = view.dataset;
            var ids = view.get_selected_ids();

            if (ids.length === 1) {
                this.dataset.call('perm_read', [ids]).done(function(result) {
                    var dialog = new session.web.Dialog(this, {
                        title: _.str.sprintf(_t("View Log (%s)"), self.dataset.model),
                        width: 400
                    }, QWeb.render('ViewManagerDebugViewLog', {
                        perm : result[0],
                        format : session.web.format_value
                    })).open();
                });
            }

        },

    });

//Check date and number
var check_and_complete_date = function (obj,input_mask,date_pattern) {
		var date_string=obj.value;

		var date_separate="";
//		console.log("OBJ:");
//		console.log(this);
//		console.log("Input");
//		console.log($("input[name='"+ obj.name + "']"));
		if (date_string.indexOf("-")>=0)
			{date_separate='-';}
		else if (date_string.indexOf("/")>=0)
			{date_separate='/';}
		else if (date_string.indexOf(".")>=0)
			{date_separate='.';}

		if (date_separate !=="")
			{
				date_array=date_string.split(date_separate);

				first=parseInt(date_array[0]);
				first=("0" + first).slice(-2);

				second=date_array[1];
				second=parseInt(second);
				update=false;

				if (isNaN(second))
					{
						//date_array_pattern=input_mask.split(date_separate);
						var curr_date = new Date();
						var curr_date_str = curr_date.toString(date_pattern.replace("MM","M"));
						second=curr_date_str.split(date_separate)[1]
						second=("0" + second).slice(-2);
						third=curr_date_str.split(date_separate)[2]
						update=true
					}
				else
					{
						third=date_array[2];
						third=parseInt(third);
						second=("0" + second).slice(-2);

						if (isNaN(third))
							{
								var curr_date = new Date();
								var curr_date_str = curr_date.toString(date_pattern.replace("MM","M"));
								third=curr_date_str.split(date_separate)[2]
								update=true
							}
						else
							{
								str_third=third.toString();
								if (str_third.length<4)
									{
										third="1"+parseInt(str_third[str_third.length-1]);
										update=true
									}
							}
					}
				if (update && !isNaN(first))
					{
					date_value=first + date_separate + second + date_separate + third;

					$(obj).val(date_value)
													.change();


					}
			}
};

var check_parent = function (obj,name_class)
	{
		var result=false;
		if (typeof(obj.parentNode) !== 'undefined')
			if (typeof(obj.parentNode.classList) !== 'undefined')
				if (obj.parentNode.classList.contains(name_class))
					result=true;
		return result;
	}



//Change return value when click to Picker date
session.web.DateWidget = session.web.DateWidget.extend ({
    on_picker_select: function(text, instance_) {
        var date = this.picker('getDate');
        this.$input
            .val(date ? this.kderp_format_client(date) : '')
            .change()
            .focus();
    },
	kderp_format_client: function(v) {
		var normalize_format = function (format) {
		    return Date.normalizeFormat(session.web.strip_raw_chars(format));
		};
    	var l10n = _t.database.parameters;
    	date_value=v.toString(normalize_format(l10n.date_format).replace("MMM","M"));
        return date_value;
    },
});

////Add InputMask for tree editable
//session.web.list.Editor= session.web.list.Editor.extend({
//    _focus_setup: function (focus_field) {
//    	 _super = this._super(focus_field);
//    	 var self=this;
//		return _super;
//    	// return $.when(_super,attach_mask_editable(self.$el.find('input'),this.record));
//    },
//
//});

//session.web.ViewManagerAction = session.web.ViewManagerAction.extend({
//
//    do_create_view: function(view_type) {
//        var self = this;
//        return this.alive(this._super.apply(this, arguments)).done(function() {
//        	if (view_type==='form')
//        		{
//					return true;
//        		setTimeout(function (){
//        				attach_mask_editable($(self.$el.find('div.oe_form')[0]).find('input[type=text]'));
//        				},500);
//        		}
//        });
//    },
//});

session.web.FormView =  session.web.FormView.extend({

	check_actual_mode: function(source, options) {
        var self = this;
        var _super=this._super(source, options);
        var showSideBar = function ()
        	{
	        	if (self.get("actual_mode") !== "view" && self.datarecord.id)
	        		self.$sidebar.show();
        	}
        return $.when(_super,showSideBar());
    },

	load_form: function(data)
		{
		var self=this;
		var objj=this;

        // DBClick to Edit mode
		var bind_event= function(evt){
				objj.$el.find(".oe_form_group_row,.oe_form_field,label").on('dblclick', function (e) {
		            if(self.get("actual_mode") === "view") {
		            	self.options.$buttons.find(".oe_form_button_edit").click();
		            	e.preventDefault();
		            }
		        });
				$(document).on('keydown',function (e) {
					if ($(".ui-dialog-content").length<=0 && ($(':focus').length===0) && e.which === 69 && self.get("actual_mode") === "view") //e.ctrlKey && !e.altKey && !e.shiftKey
						{
						//console.log($(':focus').parent());
						self.options.$buttons.find(".oe_form_button_edit").click();
						e.preventDefault();
						}
					else if (e.ctrlKey && !e.altKey && !e.shiftKey && e.which === 68) //Duplicate when Ctrl+D
						{
							e.preventDefault();
//							console.log(self.options.$sidebar);
							//return self.guard_active(self.on_button_duplicate(self));
						}
					else if(e.ctrlKey && !e.altKey && !e.shiftKey && e.which === 83) // Check for the Ctrl key being pressed, and if the key = [S] (83)
						if(self.get("actual_mode") === "edit")
							{
							e.preventDefault();
							var save_mode=self.options.$buttons.find(".oe_form_button_save").click();
							setTimeout(function(){
								$('<div>')
							      .attr('class', 'kderp_oe_notification')
							      .html("<div class='.openerp .kderp_oe_notification'></div>")
							      .fadeIn('fast')
							      .insertAfter($('.oe_loading'))  //<== wherever you want it to show
							      .animate({opacity: 1.0}, 1000)     //<== wait 3 sec before fading out
							      .fadeOut('slow', function()
							      {
							        $(this).remove();
							      });
									self.options.$buttons.find(".oe_form_button_edit").click();
									},500);
							}
		        });
				//Always in Edit Mode
				if(self.get("actual_mode") === "view") {
					setTimeout(function(){return self.options.$buttons.find(".oe_form_button_edit").click();},500);
		        }
		};

		var _super=this._super(data);
		return $.when(_super,bind_event())
	}
    });

/*
 * Sua phan xoa line o trong List many2one
 * Bi loi khi nhap budget, do list view se cap nhat du lieu theo tu tu sua, vi vay khi them 1 dong vao roi xoa 1 dong
 * Khi commit ma co rang buoc trung du lieu thi se bao loi do co 2 ban ghi trung nhay
 * Sua lai de cho phan xoa len tren cung
 * */
session.web.DataSet.include({
	write: function (id, data, options) {
		 _.each(data, function (dat) {
             if (dat instanceof Object)
                     dat.sort(function (rd) {
                             switch(rd) {
                                     case 2: return 0
                                     case 3: return 1
                                     case 1: return 2
                                     case 0: return 3
                                     case 4: return 4
                                     }
                             return 5

                     })});
		 return this._super(id, data, options);
	},
});

session.web.search.InputView = session.web.search.InputView.extend({
    //init: function (parent, model) {
    //    this._super(parent,model);
		//this.$el.draggable();
		//console.log(this);
    //},
	onKeydown: function (e) {
		var _super=this._super(e);
		   switch (e.which) {
	        case $.ui.keyCode.ESC:
	        	e.preventDefault();
	        	preceding.model.destroy();
	            break;
		   }
		return _super;
	}

});

/**
 * start
 * An cua so search khi di roi con tro chuot
 * Su dung timer de cancel event khi su kien xay ra lien tiep trong khoang thoi gian delay
 * vi du: di chuyen chuot lien tuc vao va ra khoi element
 * De cho o search co the drag duoc
 *
 * select_completion
 * Dinh dang cach hien thi Ngay va So khi go o phan search. Them phan tim kiem theo khoang, tim kiem not o phan search
 * setup_global_completion
 * Dieu chinh phan delay cua search tu 250 xuong 0 -- more responsive
 * TODO
 *
 * build_search_data
 * Them dieu kien search hoac (or) cho cac filter da co san
 * Kiem tra dieu kien search nhap vao neu co chua || thi se them vao domain search
 * dieu kien hoac
 */

session.web.SearchView = session.web.SearchView.extend(/** @lends instance.web.SearchView# */{
    start: function () {
        var self = this;
        this._super(this);
		this.$el.draggable({containment: this.$el.parents('.oe_header_row')});

        time_to_leave = 2500;
        var timer;
        this.$el.find('.oe_searchview_drawer').on('mouseleave', function(){
        	timer = setTimeout(function(){
        		self.$el.toggleClass('oe_searchview_open_drawer', false);
        	},1000)
        });
        this.$el.find('.oe_searchview_drawer').on('mouseenter', function(){
        	clearTimeout(timer);
        });
    },

	select_completion: function (e, ui) {
		var filter_value=ui.item.facet.values[0].actual_value;

		var type_value='string';

		if (typeof(filter_value) === 'undefined')
			{
			filter_value=ui.item.facet.values[0].value;
			}
		else if (typeof(filter_value) === 'object')
			{
			var type_filter = filter_value.value_type;
			//Date Area
			if (type_filter==='range_date')
				{
					var from_string=filter_value.date.toString('dd-MMM-yyyy');
					var to_string=filter_value.to_date.toString('dd-MMM-yyyy');
					var string_label="Range :" + from_string+"~"+to_string;

					filter_value=filter_value.date.toString('yyyy-MM-dd')+"~"+filter_value.to_date.toString('yyyy-MM-dd');
					type_value='date';
				}
			else if (type_filter==='greater_date')
				{
				var from_string=filter_value.date.toString('dd-MMM-yyyy');
				var string_label=greater_than_str + from_string;

				filter_value=filter_value.date.toString('yyyy-MM-dd')+"~";
				type_value='date';
				}
			else if (type_filter==='less_date')
				{
				var to_string=filter_value.to_date.toString('dd-MMM-yyyy');
				var string_label=less_than_str + to_string;

				filter_value="~"+filter_value.to_date.toString('yyyy-MM-dd');
				type_value='date';
				}
			//Number Area
			else if (filter_value.type==='number')
				{
					type_value='number';
					if (type_filter==='greater_number')
						{
							filter_value=filter_value.from_number.toString()  + "~";
						}
					else if (type_filter==='less_number')
						{
							filter_value="~" + filter_value.to_number.toString();
						}
					else
						{
							filter_value=filter_value.from_number.toString() + "~" + filter_value.to_number.toString();
						}
				}
			}

		var original_value=filter_value;
		var filter_domain="";

		ui.item.facet.field.view.fields_view.arch.children.forEach(function (value) {
			if (ui.item.facet.field.attrs['string'] === value.attrs.string && ui.item.facet.field.attrs['name'] === value.attrs.name)
				{
				filter_domain=value.attrs.filter_domain;
				}
		});

		if (typeof(filter_value)==='string')
			{
				var prefix="";
				filter_value=filter_value.toUpperCase();
				if (filter_value.search(/\\/)>0 && filter_value.search("~")>2)
		    		{
			    		prefix=filter_value.split(/\\(.+)?/)[0];
			    		range=filter_value.split(/\\(.+)?/)[1];

			    		from_value=range.split("~")[0]
			    		to_value=range.split("~")[1]

			    		from_value=prefix.trim()+from_value
			    		to_value=prefix.trim()+to_value

			    		filter_value="\\" + from_value + "~" + to_value;

		    		}
				if (['date','number'].indexOf(type_value)>=0 && filter_value.search("~")>=0)
					{

					//prefix1=filter_value.split("\\")[0];
		    		range_value=filter_value;

		    		from_value=range_value.split("~")[0]
		    		to_value=range_value.split("~")[1]

		    		field_name=ui.item.facet.field.attrs['name'];
		    		if (type_value==='number')
		    			{
		    			if (type_filter==='greater_number')
		    				{
			    				filter_domain="[('" + field_name +"','>=',"+from_value+")]";
				    			//filter_domain=filter_domain+",('" + field_name +"','<=',"+to_value+")]";
		    				}
		    			else if (type_filter==='less_number')
		    				{
			    				//filter_domain="[('" + field_name +"','>=',"+from_value+")";
				    			filter_domain="[('" + field_name +"','<=',"+to_value+")]";
		    				}
		    			else
		    				{
			    				filter_domain="[('" + field_name +"','>=',"+from_value+")";
				    			filter_domain=filter_domain+",('" + field_name +"','<=',"+to_value+")]";
		    				}
		    			}
		    		else if (type_filter==='greater_date')
		    			{
			    			filter_domain="[('" + field_name +"','>=','"+from_value+"')]";
	//		    			filter_domain=filter_domain+",('" + field_name +"','<=','"+to_value+"')]";
		    			}
		    		else if (type_filter==='less_date')
	    				{
			    			//filter_domain="[('" + field_name +"','>=','"+from_value+"')";
			    			filter_domain="[('" + field_name +"','<=','"+to_value+"')]";
	    				}
		    		else
	    				{
			    			filter_domain="[('" + field_name +"','>=','"+from_value+"')";
			    			filter_domain=filter_domain+",('" + field_name +"','<=','"+to_value+"')]";
	    				}
					//ui.item.facet.field.attrs.filter_domain=filter_domain;

					ui.item.facet.category= ui.item.facet.category + new Date().getTime();

					//ui.item.facet.field.attrs.filter_domain=filter_domain;
					//filter_value = filter_value.replace("!!", "");
					ui.item.facet.values[0].value = original_value;
					//ui.item.facet.filter_domain=filter_domain;
					if (typeof(string_label)==='undefined')
						{
						ui.item.facet.values[0].label = "Range :" + from_value + "~" + to_value;
						}
					else
						{
						ui.item.facet.values[0].label=string_label;
						}

					}
				else if (filter_value.search(/\\/)===0 && filter_value.search("~")>2)
						{
							prefix1=filter_value.split(/\\/)[0];
				    		range_value=filter_value.split(/\\/)[1];

				    		from_value=range_value.split("~")[0]
				    		to_value=range_value.split("~")[1]

				    		field_name=ui.item.facet.field.attrs['name'];
				    		if (type_value==='number')
				    			{
				    			filter_domain="[('" + field_name +"','>=',"+from_value+")";
				    			filter_domain=filter_domain+",('" + field_name +"','<=',"+to_value+")]";
				    			}
				    		else
				    			{
				    			filter_domain="[('" + field_name +"','>=','"+from_value+"')";
				    			filter_domain=filter_domain+",('" + field_name +"','<=','"+to_value+"')]";
				    			}
							//ui.item.facet.field.attrs.filter_domain=filter_domain;

							ui.item.facet.category= ui.item.facet.category + new Date().getTime();

							//ui.item.facet.field.attrs.filter_domain=filter_domain;
							//filter_value = filter_value.replace("!!", "");
							ui.item.facet.values[0].value = original_value;
							//ui.item.facet.filter_domain=filter_domain;
							if (typeof(string_label)==='undefined')
								{
								ui.item.facet.values[0].label = "Range :" + from_value + "~" + to_value;
								}
							else
								{
								ui.item.facet.values[0].label=string_label;
								}
						}
				//Search NOT

		        if (filter_value.search("!!")===0 && typeof(filter_domain)!=='undefined' && typeof(filter_domain)==="string")
		        	{
		        		var find_replace_condition = function (filter_domain, vFind, vRplace)
		        		{
			        		tmp_filter_domain=filter_domain.split(vfind);
			        		for (var i=0; i < tmp_filter_domain.length; i++)
			        		    {
			        				tmp_filter_domain[i].split(vReplace).join(vFind);
			        		    }
		        			return tmp_filter_domain.join(vRplace);
		        		};

			        	ui.item.facet.category= ui.item.facet.category + new Date().getTime();

			        	filter_domain=filter_domain.split(", ").join(",");
			        	filter_domain=filter_domain.split(" ,").join(",");
			        	vfind=",'=',";
			        	vReplace=",'!=',";
			        	filter_domain=find_replace_condition(filter_domain,vfind,vReplace);

			        	vfind=",'ilike',"
			        	vReplace=",'not ilike',"
			        		filter_domain=find_replace_condition(filter_domain,vfind,vReplace);

			        	vfind=",'in',"
			        	vReplace=",'not in',"
		        		filter_domain=find_replace_condition(filter_domain,vfind,vReplace);
			        	 if (filter_value.indexOf("!!")===0)
			        		{
								filter_value = filter_value.replace("!!", "");
								ui.item.facet.values[0].value=filter_value;
								ui.item.facet.values[0].label="!" +filter_value;
			        		}
		        	}
			}
		ui.item.facet.filter_domain=filter_domain;
        ui.item.facet.field.attrs.filter_domain=filter_domain;
        //console.log(filter_domain);
        var _super=this._super(e,ui);
        return _super;
    },

    setup_global_completion: function(){
    	this._super();
        var autocomplete = this.$el.autocomplete({
            source: this.proxy('complete_global_search'),
            select: this.proxy('select_completion'),
            focus: function (e) { e.preventDefault(); },
            html: true,
            autoFocus: true,
            minLength: 1,
            delay: 0, //original value is 250
        }).data('autocomplete');
    },

	build_search_data: function () {
            var _super = this._super();
            var domains = _super.domains;

            if (domains.length>=1)
				{
					//Chuyen domain thanh string
					convertDomaintoString = function(domain) {
						if (domain.eval === undefined)
							if ($.type(domain) === 'string')
								return domain;
							else
								return JSON.stringify(domain);
						else
							return JSON.stringify(domain.eval());
					};
					var searchDomain = convertDomaintoString(domains[domains.length-1]);

                if (searchDomain.indexOf('"||')>=0 || searchDomain.indexOf("'||")>=0) {
                    searchDomain = searchDomain.replace(/\'\|\|/g,"'").replace(/\"\|\|/g,'"');

                    sDomain0 = convertDomaintoString(domains[0]);
					sDomain0 = py.eval(sDomain0);
					sDomain1 = py.eval(searchDomain);

					pos = sDomain0.indexOf('|');
                    if (pos < 0)
                        sDomain0.splice(sDomain0.length - 1, 0, '|');
                    else
                        sDomain0.splice(pos, 0, '|');
                    sDomain0 = sDomain0.concat(sDomain1);
					//console.log(sDomain0);
                    domains.pop();
                    domains[0] = JSON.stringify(sDomain0);

                }
			}
			return _super;
        },
    });


//Chuyen domain cua tung facet vao search
session.web.search.Field.include({

    get_domain: function (facet) {
    	this.attrs['filter_domain']=facet.attributes['filter_domain'];
        return this._super(facet);
    }
});

//Show Number Field if match Pattern
session.web.search.NumberField = session.web.search.NumberField.include(/** @lends instance.web.search.NumberField# */{
    complete: function (needle) {

        var range=_t("");
        if (typeof(needle)==='string')
    		if (needle.search("~")>=0)
    	    			{
    	    			from_amount=needle.split('~')[0].split(" ").join("").split(",").join("")
    	    			to_amount=needle.split('~')[1].split(" ").join("").split(",").join("")
    	    			var val = this.parse(from_amount);
    	    			var tval = this.parse(to_amount);

    	    			if (val && tval) //Neu co ca a~b
    	    				{
    	    					range=_t("Range ");
    	    					var return_value={'value_type':'number','type':'number','from_number':val,'to_number':tval};
    	    					var number_string= range + ":" + val.toLocaleString() + "~" + tval.toLocaleString();
    	    				}
    	    			else if (val) //Neu co ca a~
    	    				{
	    	    				var return_value={'value_type':'greater_number','type':'number','from_number':val,'to_number':tval};
		    					var number_string= greater_than_str + val.toLocaleString();
    	    				}
    	    			else if (tval) //Neu co ca ~b
    	    				{
	    	    				var return_value={'value_type':'less_number','type':'number','from_number':val,'to_number':tval};
		    					var number_string= less_than_str + tval.toLocaleString();
    	    				}
    	    			else
    	    				val = undefined
    	    			}
	    		else
	    			{
	    			var val = this.parse(needle.split(" ").join("").split(",").join(""));
	    			var number_string= val.toLocaleString();
	    			}
    	else
    		{
	    		var val = this.parse(needle.split(" ").join("").split(",").join(""));
	    		var number_string= val.toLocaleString();
    		}

        if (isNaN(val)) { return $.when(); }
        var label = _.str.sprintf(
            _t("Search %(range)s%(field)s for: %(value)s"), {
            	range: range,
                field: '<em>' + this.attrs.string + '</em>',
                value: '<strong>' + number_string  + '</strong>'});
        return $.when([{
            label: label,
            facet: {
                category: this.attrs.string,
                field: this,
                values: [{label: number_string, value: val, actual_value:return_value}]
            }
        }]);
    },
});

//Show Date Field if match Pattern
session.web.search.DateField = session.web.search.DateField.extend(/** @lends instance.web.search.DateField# */{
    value_from: function (facetValue) {
    	if (typeof(facetValue.get('value'))==='string')
    		return true;
    	else
    		return this._super(facetValue);
    },
    complete: function (needle) {
    	var check_date=false;
    	var range="";

    	if (typeof(needle)==='string')
    		if (needle.search("~")>=0)
    			{
    			//needle=needle.split('\\')[1];
    			from_date=needle.split('~')[0]
    			to_date=needle.split('~')[1]
    			var d = Date.parse(from_date);
    			var td = Date.parse(to_date);

    			if (td && d)
    				{
    				check_date=true;
    				var range=_t("Range ");
    				var return_value={'value_type':'range_date','type':'range_date','date':d,'to_date':td};
    				var date_string = d.toString("dd-MMM-yyyy") + "~" + td.toString("dd-MMM-yyyy")
    				}
    			else if (d) //Greater Than
    				{
    				check_date=true;
    				var range=_t("");
    				var return_value={'value_type':'greater_date','type':'range_date','date':d};
    				var date_string = "Greater Than " + d.toString("dd-MMM-yyyy")
    				}
    			else if (td) //Less Than
    				{
    				var range=_t("");
    				check_date=true;
    				var return_value={'value_type':'less_date','type':'range_date','to_date':td};
    				var date_string = "Less Than " + td.toString("dd-MMM-yyyy")
    				}
    			}
    		else
    			{
    			var d = Date.parse(needle);
    			if (d)
    				{check_date=true;
    				var date_string =  d.toString("dd-MMM-yyyy");
    				var return_value={'type':'date','date':d};
    				}
    			}
    	else
    		{
    			var d = Date.parse(needle);
    			if (d)
    				check_date=true;
    			var date_string =  d.toString("dd-MMM-yyyy");
    		}
    	if (!check_date) { return $.when(null); }
        var label = _.str.sprintf(_.str.escapeHTML(
            _t("Search %(range)s%(field)s at: %(value)s")), {
        		range: range,
                field: '<em>' + this.attrs.string + '</em>',
                value: '<strong>' + date_string + '</strong>'});
        return $.when([{
            label: label,
            facet: {
                category: this.attrs.string,
                field: this,
                values: [{label: date_string, value: d, actual_value:return_value}]
            }
        }]);
    }
});

//Open New Tab instead of PopUp
var open_new_tab = function (data,target,kd_context1)
	{
//		console.log('NEW');
		window.kd_context=kd_context1;
		var x_open = window.open(data['server']+"/?#id="+data['id']+"&view_type=form&model="+data['model'], target);
		return x_open;
	};

//session.web.form.SelectCreatePopup = session.web.form.SelectCreatePopu1p.extend({
//	new_object: function() {
// 		var self=this;
// 		return $.when(self._super()).then(function () {
//				return true;
// 				setTimeout(function(){
// 					attach_mask_editable($('div.ui-dialog-content.ui-widget-content').find("input[type='text']"));
// 				},500);
// 				});
// 	},
//});

//Click to Tree View
session.web.form.AbstractFormPopup1 = session.web.form.AbstractFormPopup.include({

	    display_popup: function() {
	    	var self=this;

	    	if (!(parseInt(this.row_id)>0 && this.options.target!=='new_popup' && ['kderp.supplier.vat.invoice','res.partner'].indexOf(self.model)<0 ))
	    		{
    			var no_return="";
    			var revalue= function (obj){
    				if (no_return!=="")
    					self.target=no_return;
    			};

	    		if (this.target==='new_popup')
	    			{
		    			this.target='new';
		    			no_return='new_popup';
	    			};
    			if (typeof(this.row_id)==='object' && this.row_id!==null)
    				{
    					this.row_id=this.row_id[0];
    				};
		    	return $.when(self._super(),revalue(this));
	    		}
	    	else
	    		{
		    		kd_context = session.web.pyeval.eval('context', this.context);
		    		window.kd_context=kd_context;
	    			window.open(this.session.server+"/?#id="+this.row_id+"&view_type=form&model="+this.model, '_blank');
	    			self.destroy();
	    		}
	    },
});

/**
 * Confirm before Delete a record in List View
 *
 * pad_table_to: bo sung de goi floating_header, delay 10ms
 *
 * floating_header: JQuery su dung de tao floating header cho tree view
 * header cua 1 bang se co dinh, khong bi cuon theo mouse
 * Bo sung them viec tinh toan lai header khi co gian man hinh
 */
session.web.ListView.List.include({
	init: function (group, opts) {
		this._super(group, opts);
		var self=this;
		this.$current.undelegate('td.oe_list_record_delete button', 'click');
		this.$current.delegate('td.oe_list_record_delete button', 'click', function (e) {
		         e.stopPropagation();
		         var $row = $(e.target).closest('tr');
		         if (self.row_id($row))
			         if (!confirm(_t("Do you really want to remove these records?"))) {
			        	 	return;
			         };
		         $(self).trigger('deleted', [[self.row_id($row)]]);
		     });
	     $(window).resize(function(){
	     	self.floating_header(self);
	     });
		},

	pad_table_to: function(count){
		this._super(count);
		var self = this;
		setTimeout(function(){
			self.floating_header(self);
		},0);

	},

//	render: function () {
//		var _super=this._super();
//		var self = this;
//		setTimeout(function(){
//			self.floating_header(self);
//		},10);
//	},

	floating_header: function(current_list){
		//Freezing table header in tree view
		//Clone headers
		if ($(".floatingHeader").length >0){ //Kiem tra floatingHeader co ton tai?
			$(".floatingHeader").remove()
			};

		if (current_list.options.search_view){
			//Kiem tra xem co phai la Tree view hay khong: co search view hay khong
			//su dung first de han che ap dung cho element dau tien, su dung clone(true) de copy event
			var $floatingHeader = $(".oe_list_header_columns").filter(":first").clone(true);
			    $floatingHeader.children().width(function (i, val) {
			    	return $(".oe_list_header_columns").filter(":first").children().eq(i).width();
			    });

		    	$floatingHeader.css({"width":$(".oe_list_header_columns").filter(":first").width()
		    		, "height":$(".oe_list_header_columns").filter(":first").height()})
		    		.addClass("floatingHeader");

		    	//$floatingHeader.css({"width", $(".oe_list_header_columns").filter(":first").width());
			    //$floatingHeader.css("height",$(".oe_list_header_columns").filter(":first").height()).addClass("floatingHeader");
			    $(".oe_list_header_columns").filter(":first").before($floatingHeader);
		};
	  },
});

/*
//Lost focus khong bi mat gia tri
session.web.form.One2ManyListView = session.web.form.One2ManyListView.extend({
	_on_form_blur: function () {
		this.__ignore_blur = true;
		return this._super();
    },
});
*/

//Keep checked when click Action
session.web.ListView.include({
	reload_content: function () {
		 var self=this;
		 var selected_ids=[];
		 var checked_all=self.$el.find('.oe_list_record_selector ').prop('checked');
		 var list_input_selected=this.$el.find('th.oe_list_record_selector input:checked').closest('tr').each(function () {
			 selected_ids.push($(this).data('id'));
		 	});
		 var _super=self._super(this);

		 return $.when(_super).done( function () {
			 	list_element_must_be_Check=[];
			 	$('th.oe_list_record_selector input').closest('tr').each(function (){
			 		if (selected_ids.indexOf($(this).data('id'))>=0)
			 			{
			 			list_element_must_be_Check.push($(this).find('input')[0]);
			 			};
			 	});
			 	self.$el.find('.oe_list_record_selector ').prop('checked',checked_all);
			 	$(list_element_must_be_Check).prop('checked',true);

			 });
	 },
});

	//Windows Action
//Pass context to Window.open
session.web.ActionManager = session.web.ActionManager.extend({

	init: function(parent) {
		var self=this;
		var _super=self._super.apply(self, arguments);
		try
			{
			if (typeof(window.opener.kd_context)!=='undefined')
				{
				if (typeof(window.opener.kd_context.executor)!=='undefined')
					{
					parent.session.user_context=window.opener.kd_context['executor'].action.context;
					}
				else
					{
					parent.session.user_context=window.opener.kd_context;
					};
				window.opener.kd_context={};
				}
			}
		catch (e)
			{
				console.log(e);//Hien thong bao loi
				return ;
				parent.session.user_context={};
			}
		return _super;
	},
//IR Windows Action with target new
	ir_actions_common: function(executor, options) {
		var tmp_action=executor.action;
		var self=this;
		if (tmp_action.tag==="change_password")
			{
				tmp_action.target='new_popup';
				var a= new session.web.ChangePassword(this);
				a.start();
			}
		if (tmp_action.res_model!='res.partner' && tmp_action.type==='ir.actions.act_window' && tmp_action.target=='new' && parseInt(tmp_action.res_id)>0)
			{
				new_tab_server = window.location.protocol+"//"+window.location.host;
				new_tab_data={'id':tmp_action.res_id,'model':tmp_action.res_model,'server':new_tab_server};
				open_new_tab(new_tab_data, '_blank',{'executor':executor,'options':options});
				return false;

			}
		else
			{
				if (tmp_action.target==='new_popup')
					executor.action.target='new';
				//var _super=self._super(executor, options);
				var _super=self._super.apply(self, arguments);
				return _super;
			}
	},
	});

/**
 * Backspace remove all
 *
 * this.$input.autocompete() ke thua ham nay de sua loi delay trong khi nhap
 * lieu o form voi cac truong Many2One doi delay: 0
 * Muon cho code gon hon nua TOD
 *
 * Luu y phan this._super(this) vs return this._super(this)
 */
session.web.form.FieldMany2One = session.web.form.FieldMany2One.extend({
	//display_string: function(str) {
	//	var res = this._super(str);
	//	var objM2O = this.$el.find('.oe_form_uri');
	//	var self = this;
	//	if (objM2O.length>0)
	//	{
	//		if (self.get("value")) {
	//			var ctx  = self.build_context();
	//			ctx.add({'show_title':1});
	//			var dataset = new session.web.DataSetStatic(this, this.field.relation, ctx);
	//			var def = this.alive(dataset.name_get([self.get("value")])).done(function (data) {
	//				if (!data[0]) {
	//					self.do_warn(_t("Render"), _t("No value found for the field " + self.field.string + " for value " + self.get("value")));
	//					return;
	//				}
	//			objM2O[0].title = data[0][1];
	//			});
	//		}
	//	}
	//	return res
	//},
	render_editable: function() {
        var self = this;
        this.$input = this.$el.find("input");
        this.$input.on('keydown',function (e) {
        	if (!e.ctrlKey && !e.altKey && !e.shiftKey && [8,46].indexOf(e.which)>=0 && self.get('value'))
        		{
        			e.preventDefault();
        			self.reinit_value(false);
        		}
        });
        this._super(this);

        this.$input.autocomplete({
            source: function(req, resp) {
                self.get_search_result(req.term).done(function(result) {
                    resp(result);
                });
            },
            select: function(event, ui) {
                isSelecting = true;
                var item = ui.item;
                if (item.id) {
                    self.display_value = {};
                    self.display_value["" + item.id] = item.name;
                    self.reinit_value(item.id);
                } else if (item.action) {
                    item.action();
                    // Cancel widget blurring, to avoid form blur event
                    self.trigger('focused');
                    return false;
                }
            },
            focus: function(e, ui) {
                e.preventDefault();
            },
            html: true,
            // disabled to solve a bug, but may cause others
            //close: anyoneLoosesFocus,
            minLength: 0,
            delay: 0
        });

//        return this._super(this);
	},
});

session.web.form.FieldMany2OneImage = session.web.form.FieldMany2One.extend({
	template: "FieldMany2OneImage",
	init: function(field_manager, node) {
		this._super(field_manager, node);
		this.vid=false;
	},
	/**
	 * Bat su kien hover len anh de phong to
	 * Su dung position: absolute de khi phong to khong anh huong den cac thanh phan khac
	 */
	events: {
		"mouseenter .koe_many2one_image": "img_enter",
		"mouseleave .koe_many2one_image": "img_leave"
	  },
	img_enter: function(){
		  this.$el.find(".koe_many2one_image").css({'width': '+=24px','height': 'auto','position':'absolute'});
	  },
	img_leave: function(){
		  this.$el.find(".koe_many2one_image").css({'width': '','height':'','position':'initial'});
	  },

	render_value: function(no_recurse) {
		var _super=this._super(no_recurse);
		var self=this;
		var url;
		field='image';
		self.vid=self.get("value");

		if (! no_recurse) {
			if (!self.get("value"))
				{
				self.$el.find('.koe_many2one_image').remove();
				}
            else
            	{
	            	var show_image = function (obj, model, vid, field)
	            		{
		            		dataset=new session.web.DataSetStatic(self, model, self.build_context());
		            		dataset.set_ids([vid]);
		            		obj.$el.find('.koe_many2one_image').remove();
		            		dataset.read_slice([field],{}).then(function (data){
		            				if (data.length>0)
		            					if (data[0][field])
		            						{
			            						url = self.session.url('/web/binary/image', {
			        		                        model: model,
			        		                        id: vid,
			        		                        field: field,
			        		                        t: (new Date().getTime()),
			        		                        });
			        			                var $img = $(QWeb.render("FieldBinaryImage-img", { widget: obj, url: url }));
			        			                obj.$el.find('.koe_many2one_image').remove();
			        			                $img.addClass('koe_many2one_image');
			        			                obj.$el.prepend($img);
			        			                $img.load(function() {
			        			                    if (! obj.options.size)
			        			                        return;
			        			                    $img.css("max-width", "" + self.options.size[0] + "px");
			        			                    $img.css("max-height", "" + self.options.size[1] + "px");
			        			                    $img.css("margin-left", "" + (self.options.size[0] - $img.width()) / 2 + "px");
			        			                    $img.css("margin-top", "" + (self.options.size[1] - $img.height()) / 2 + "px");
			        			                	});
		            						}
		            			});
	            		};

	            	if (self.options.preview_image)
	            		{
	            			var dataset = new session.web.DataSetStatic(self, self.field.relation, self.build_context());
		            		field_temp=self.options.preview_image;
		            		parent=field_temp.split('/')[0];
		            		field=field_temp.split('/')[1];
		            		if (typeof (field)!=='undefined')
		            			{
		            			dataset.set_ids([self.get("value")]);
		            			dataset.read_slice([parent],{}).then(function(data) {
		            				if (data.length>0)
		            					{
		            						if (self.options.model)
		            							show_image(self, self.options.model, data[0].employee_id[0], field);
		            						else
		            							show_image(self, dataset.model, data[0].employee_id[0], field);
		            					}
		                    		});
		            			}
		            		else
		            			{
		            			field=parent;
		            			if (self.options.model)
			            			show_image(self, self.options.model, self.vid, field);
		            			else
		            				show_image(self, self.field.model, self.vid, field);

		            			}
	            		}
	            	else
	            		{
	            		if (self.options.model)
	            			show_image(self, self.options.model, self.vid, field);
            			else
            				show_image(self, self.field.model, self.vid, field);
	            		}
            	};
		}

	return _super;
	},
});



/*
	Add inputmask to float field, Date
*/
session.web.form.FieldDate = session.web.form.FieldDate.extend({
	render_value: function() {
		var self = this;
		if (this.get("effective_readonly"))
			return this._super();
		else
			return $.when(this._super(),attach_mask_editable(self.$el.find('input')));
	},
});

session.web.form.FieldFloat = session.web.form.FieldFloat.extend({
	render_value: function() {
		var self = this;
		if (this.get("effective_readonly"))
			return this._super();
		else
			return $.when(this._super(),attach_mask_editable(self.$el.find('input')));
	},
});
//
//session.web.DateWidget = session.web.DateWidget.include({
//
//});

//Add widget as a progress bar on readyonly
//Extend for progressfloat - ke thua thiet ke cua progressbar
session.web.form.widgets.add ('progressfloat','session.web.form.progressfloat');
session.web.form.progressfloat = session.web.form.FieldFloat.extend({
	template: "FieldProgressBarFloat",
	render_value: function() {
		if (this.get("effective_readonly"))
			{
		        this.$el.progressbar({
		            value: this.get('value') || 0,
		            disabled: this.get("effective_readonly")
		        });
		        var formatted_value = session.web.format_value(this.get('value') || 0, { type : 'float' });
		        this.$('span').html(formatted_value + '%');
			}
		else
			return this._super();
	}

});

//
session.web.form.One2ManyList=session.web.form.One2ManyList.extend({
    pad_table_to: function (count) {
        if (!this.view.is_action_enabled('create')) {
            this._super(count);
        } else {
            this._super(count > 0 ? count - 1 : 0);
        }

        // magical invocation of wtf does that do
        if (this.view.o2m.get('effective_readonly')) {
            return;
        }

        var self = this;
        var columns = _(this.columns).filter(function (column) {
            return column.invisible !== '1';
        }).length;
        if (this.options.selectable) { columns++; }
        if (this.options.deletable) { columns++; }

        if (!this.view.is_action_enabled('create')) {
            return;
        }

        var $cell = $('<td>', {
            colspan: columns,
            'class': 'oe_form_field_one2many_list_row_add'
        }).append(
            $('<a>', {href: '#'}).text(_t("Add an item"))
                .mousedown(function () {
                    // FIXME: needs to be an official API somehow
                    if (self.view.editor.is_editing()) {
                        self.view.__ignore_blur = true;
                    }
                })
                .click(function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // FIXME: there should also be an API for that one
                    if (self.view.editor.form.__blur_timeout) {
                        clearTimeout(self.view.editor.form.__blur_timeout);
                        self.view.editor.form.__blur_timeout = false;
                    }
                    self.view.ensure_saved().done(function () {
                        self.view.do_add_record();
                    });
                }));

        var $padding = this.$current.find('tr:first');
        var $newrow = $('<tr class="check_added_to_top">').append($cell);
        $padding=this.view.$el.find('thead:first');

        if ($padding.length===1 && this.$current.find('tr').length>=6) {
        	if (this.view.$el.find('tr.check_added_to_top').length===0)
        		$padding.append($newrow);
        	else
        		return ;
        } else {
        	return ;
        }
    },
});

//Sua gia tri cau o Tag
session.web.form.FieldMany2ManyTags = session.web.form.FieldMany2ManyTags.extend({

	initialize_content: function() {
			var _super=this._super(this);
			var  self = this;
			self.$text = this.$("textarea");

			var bind_x = function () {
			self.$text
				//.textext({ plugins: 'tags' })
				.bind('tagClick', function(e, tag, value, callback)
			        {
			            var pop = new session.web.form.FormOpenPopup(self);
						pop.show_element(
				                self.field.relation,
				                [value['id']],
				                self.build_context(),
				                {
				                    title: _t("Editing VAT"),
				                    target:'new_popup',
				                }
				            );
				            pop.on('write_completed', self, function(){
				            	//if(newValue)
				            	//	callback(newValue, true);
				                //self.display_value = {};
				                self.render_value();
				                self.focus();
				                self.view.do_onchange(self);
				                self.trigger('changed_value'); //Cap nhat onchange khi thay doi value
				            });
			        });

			self.$text.on('keydown', function (e) {
				if (e.which === 69 && e.ctrlKey && e.shiftKey)
					{
					e.preventDefault();
					var pop = new session.web.form.FormOpenPopup(self);
					pop.show_element(
			                self.field.relation,
			                self.get("value"),
			                self.build_context(),
			                {
			                    title: _t("Editing VAT"),
			                    target:'new_popup',
			                }
			            );
			            pop.on('write_completed', self, function(){
			                self.display_value = {};
			                self.render_value();
			                self.focus();
			                self.view.do_onchange(self);
			                self.trigger('changed_value'); //Cap nhat onchange khi thay doi value
			            });
					}
			});
			}
			return $.when(_super,bind_x());
			},
});

//Dat Default cho Base Import
session.web.DataImport = session.web.DataImport.extend({
	init: function (parent, action) {
		var _super=this._super(parent,action);
		var self=this;
		if (typeof(self.res_model)!=='undefined')
			if (self.res_model.search('purchase.order')>=0)
				self.opts[2].value='@';
		return _super;
	}
});


session.web.CrashManager = session.web.CrashManager.extend({
		show_warning: function(error) {
			if (error.type==='Session Expired')
				{
				return window.location.reload();
				};
			return this._super(error);
		},
});


session.web.WebClient.include({
    bind_hashchange: function() {
    	$(document).keydown(function (evt)
    			{
					if (!evt.shiftKey && evt.which===191 && evt.ctrlKey && !evt.altKey)//&& $(':focus').length===0
						{
							if ($('#koe_dialog_help').length===0)
								{
								show_help_dialog();
								}
							else
								{
								$('#koe_dialog_help').dialog('close');
								}
							evt.preventDefault();
						};
    			});
        this._super.apply(this, arguments);
    },
});


session.web.UserMenu =  session.web.UserMenu.extend({
    do_update: function () {
        var self = this;
        var fct = function() {
            var $avatar = self.$el.find('.oe_topbar_avatar');
            $avatar.attr('src', $avatar.data('default-src'));
            if (!self.session.uid)
                return;
            var func = new session.web.Model("res.users").get_func("read");
            return self.alive(func(self.session.uid, ["name", "company_id",'employee_id'])).then(function(res) {
                var topbar_name = res.name;
                if(session.session.debug)
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, session.session.db);
                if(res.company_id[0] > 1)
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, res.company_id[1]);
                self.$el.find('.oe_topbar_name').text(topbar_name);
                if (!session.session.debug) {
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, session.session.db);
                }
                employee_id=false;
                if (res.employee_id)
                	employee_id=res.employee_id[0]
                var avatar_src = self.session.url('/web/binary/image', {model:'hr.employee', field: 'image_small', id: employee_id});
                $avatar.attr('src', avatar_src);
            });
        };
        this.update_promise = this.update_promise.then(fct, fct);
    },
});

//Dialog Help
var show_help_dialog = function () {
	 var new_dialog=document.createElement('div');
//	 new_dialog.innerHTML='<div id="koe_dialog_help" title="Keyboard Shortcuts" class=""></div>';
	 $(new_dialog)
	 		.load('/kderp_web/static/src/xml/kderp_help.html')
	 		.attr("title","Keyboard Shortcuts")
	 		.attr("class",'koe_dialog_help')
	 		.attr("id",'koe_dialog_help')
	 		.dialog(
			    {
			        autoOpen: false,
			        resizable: false,
			        closeOnEscape: true,
			        close: function () { $(this).remove() },
			        draggable: false,
			        modal: true,
			        width: $(window).width()*90/100.0,
		            height:$(window).height()*90/100.0
			     }).parent()
			     			.addClass('koe_dialog_help')
			     			.find('div.ui-dialog-titlebar').attr("id",'koe_dialog_help_title');


	 $(new_dialog).dialog('open');
	};

//setTimeout template - replace for $(document).ready()
/*
setTimeout(function(){

},500);
 */

//Thanh added

//Cap nhat vi tri cua headers
function UpdateTableHeaders() {
	   $(".oe_list_content").each(function() {

	       var el             = $(this),
	           offset         = el.offset(),
	           scrollTop      = $(window).scrollTop()+121,
	           floatingHeader = $(".floatingHeader", this)
	       if ((scrollTop > offset.top) && (scrollTop < offset.top + el.height())) {
	    	   floatingHeader.css({
	            "visibility": "visible"
	           });
	       } else {
	           floatingHeader.css({
	            "visibility": "hidden"
	           });
	       };
	   });
	}

setTimeout(function(){
	//Test bounce effect
	/*$('.oe_footer').mouseenter(function(){
		$(this).effect('bounce',{times:3},500);
	});*/

	//Hieu ung text cho Chuc mung
	/*var greeting = "___Happy Women's Day!___";
	greeting = "<span class='greeting'>" + greeting + "</span>"
	$(".oe_breadcrumb_item:last-child").append(greeting);
	*/

	//Footer information
//	footerInfo = "Developed by <span style='color:green;font-weight:bold'>KDVN - IT</span>"
//	footerInfo = "<div>" + footerInfo + "</div>"
//	$(".oe_footer").append(footerInfo)

	//Temporary notification - replace the logo position 243x88 | 249x94
//	$(document).ready( function(){
//		$.fn.snow();
//	});
//
	tempNoti = "";
	tempPic =""; //http link of a picture - dropbox?
	if(tempPic!=""){ //Kiem tra bien rong hay khong
		$(".oe_logo img").attr("src",tempPic); //Doi duong dan cua logo
		$(".oe_logo img").css({"width":"243px","height":"88px","margin":"0px"}); //format lai cho dep - margin
	};

},2000);

//var tree_ready = function(current_list){
//	return true;
//	//Freezing table header in tree view
//	//Clone headers
//	if ($(".floatingHeader").length >0){ //Kiem tra floatingHeader co ton tai?
//		$(".floatingHeader").remove()
//		};
//
//	if (current_list.options.search_view){//Kiem tra xem co phai la Tree view o trong form hay khong
//		//su dung first de han che ap dung cho element dau tien, su dung clone(true) de copy event
//		var $floatingHeader = $(".oe_list_header_columns").filter(":first").clone(true);
//		    $floatingHeader.children().width(function (i, val) {
//		    	return $(".oe_list_header_columns").filter(":first").children().eq(i).width();
//		    });
//
//	    	$floatingHeader.css({"width":$(".oe_list_header_columns").filter(":first").width()
//	    		, "height":$(".oe_list_header_columns").filter(":first").height()})
//	    		.addClass("floatingHeader");
//
//	    	//$floatingHeader.css({"width", $(".oe_list_header_columns").filter(":first").width());
//		    //$floatingHeader.css("height",$(".oe_list_header_columns").filter(":first").height()).addClass("floatingHeader");
//		    $(".oe_list_header_columns").filter(":first").before($floatingHeader);
//	};
//  };


	/**
	 * Dieu chinh chieu ngang cua menu topbar cho gon lai de
	 * dung cho notification
	 *
     * Reflow the menu items and dock overflowing items into a "More" menu item.
     * Automatically called when 'menu_loaded' event is triggered and on window resizing.
   */
  session.web.Menu.include({
	    reflow: function() {
	    	var self = this;
	        this.$el.height('auto').show();
	        var $more_container = this.$('.oe_menu_more_container').hide();
	        var $more = this.$('.oe_menu_more');
	        $more.children('li').insertBefore($more_container);
	        var $toplevel_items = this.$el.children('li').not($more_container).hide();
	        $toplevel_items.each(function() {
	            //var remaining_space = self.$el.parent().width() - $more_container.outerWidth();
	        	var remaining_space = self.$el.parent().width()*0.8 - $more_container.outerWidth();
	            self.$el.parent().children(':visible').each(function() {
	                remaining_space -= $(this).outerWidth();
	            });
	            if ($(this).width() > remaining_space) {
	                return false;
	            }
	            $(this).show();
	        });
	        $more.append($toplevel_items.filter(':hidden').show());
	        $more_container.toggle(!!$more.children().length);
	        // Hide toplevel item if there is only one
	        var $toplevel = this.$el.children("li:visible");
	        if ($toplevel.length === 1) {
	            $toplevel.hide();
	        }
	    },
  });


  session.web.UserMenu = session.web.UserMenu.extend({
	  /**
	   * Ke thua on_menu_about de khi
	   * click vao About thi chuyen luon sang Developer Mode
	   */
	    on_menu_about: function() {
	    	if (window.location.href.search("debug")==-1){
            	window.location = $.param.querystring( window.location.href, 'debug');
	    	} else {
	    		window.location = window.location.href.replace("debug","");
	    	};
	    },

	    /**
	     * Huong dan su dung cua KDVN
	     */
	    on_menu_help: function() {
	        window.open('https://docs.google.com/document/d/1nLNlWfbR8gCEodgGw9xjeYElTvnmoT_gac5ADejRn0s/pub', '_blank');
	    },

	    on_menu_password: function() {
	        var self = this;
	        if (!this.getParent().has_uncommitted_changes()) {
	            self.rpc("/web/action/load", { action_id: "kderp_web.action_change_password" }).done(function(result) {
	                result.res_id = session.session.uid;
	                self.getParent().action_manager.do_action(result);
	            });
	        }
	    },
  });

  /**
   * Tao su kien hover cho koe_many2one_image
   */
  /*session.web.form.FieldMany2OneImage = session.web.form.FieldMany2OneImage.extend({
	  events: {
		"mouseenter .koe_many2one_image": "img_enter",
		"mouseleave .koe_many2one_image": "img_leave"
	  },
	  img_enter: function(){
		  this.$el.find(".koe_many2one_image").css({width: '+=24px',height: 'auto'});
	  },
	  img_leave: function(){
		  this.$el.find(".koe_many2one_image").css({width: '',height:''});
	  }
  });*/



  /**
   * Sua lai ham configure_pager trong ListView
   * Thay the chuoi 1-80 of xxxx bang chuoi 1-80|xxxx cho gon
   *
   * Su dung cu phap $.extend(this.PROPERTY, {NEW VALUE})o trong init
   * de them cac value moi vao
   *
   * load_list ke thua de sua loi hien thi so trang
   */
  session.web.ListView.include({

	  init: function(parent, dataset, view_id, options) {
	    var self = this;
	    this._super(parent, dataset, view_id, options);
	    $.extend(this.events,{'mouseenter thead tr.oe_list_header_columns':'header_hover'});
	    //_.extend(source, destination) dung de them doi tuong vao trong doi tuong
	  },

	  configure_pager: function(dataset){
		this._super(dataset);
		var spager_replace = this.$pager.find('.oe_list_pager_state').text().replace(" of ","|");
		this.$pager.find('.oe_list_pager_state').text(spager_replace);
	  },

	  header_hover: function(){
		  //console.log("hovering over my head...");
	  },

	  load_list: function(data){
		  var self = this;
		  this._super(data);
		  $(".oe_list_header_columns").addClass("TEST");
//		  console.log(this.$el.find(".oe_list_header_columns");
	  },

	  view_loading: function(r){
		  var self = this;
		  this._super(r);
	  },

  });

  /**
   * Ke thua class WebClient
   *
   * show_login: bo sung kiem tra kich thuoc man hinh
   * co the la 1 loat cac kiem tra khac truoc khi cho chay ung dung:
   * TODO: browser; windows
   *
   * show_application: kiem tra chieu ngang man hinh
   *
   * kderp_drawlayout: de tinh toan gia tri min-width cua oe_lefbar
   * CSS khong hoan hao trong truong hop nay do co 1 so element su dung fixed position
   *
   * kderp_refresh: su dung khi co gian man hinh
   * TODO: can refresh ca floating_header
   *
   */
  session.web.WebClient.include({
	  start: function(){
	  	var self = this;
	  	this._super();
	  	$(window).resize(function(){
	  		self.kderp_drawlayout(self);
	  	});
	  },
	  show_login: function(){
		if (screen.width >= 1024){ //1920?
	        this.toggle_bars(false);

	        var state = $.bbq.getState(true);
	        var action = {
	            type: 'ir.actions.client',
	            tag: 'login',
	            _push_me: false,
	        };

	        this.action_manager.do_action(action);
	        this.action_manager.inner_widget.on('login_successful', this, function() {
	            this.show_application();        // will load the state we just pushed
	        });
		} else {
			alert("The monitor is too small - Please adjust to at least 1024 width! - THANK YOU");
			return;
		};
    },

    show_application: function(){
    	var self = this;
    	this._super();
    	this.kderp_drawlayout(self);

    },

    kderp_drawlayout: function(container){
    	var window_width = $(window).width();
    	var leftbar_ratio = 18;
    	var leftbar_min_width = (window_width*leftbar_ratio)/100;
    	container.$el.find(".openerp .oe_leftbar").css({"min-width":leftbar_min_width});
    	container.$el.find(".openerp .oe_logo").width($(".openerp .oe_leftbar").width());
    	$(".openerp .oe_leftbar .koe_leftbar").width($(".openerp .oe_leftbar").width());
    	$(".openerp .oe_leftbar .koe_leftbar").height($(window).height()-($(".oe_topbar").height()+$(".oe_logo").height()+$(".oe_footer").height()));
    },

  });

  /**
   * Customize Search View
   * Khi click vao mot dieu kien search co the sua duoc de search tiep
   * Luu y: su dung ham trim() de remove cac ky tu thua de gay loi khi search
   * TODO: sua truc tiep tai search value va cap nhat lai search
   * Ke thua start de them thuoc tinh draggable va event dragstart de bat co dang bat dau keo tha
   * va se khong thuc hien su kien click khi keo tha
   */
  session.web.search.FacetView.include({
  	init: function(parent, model){
  		var self = this;
  		this._super(parent, model);
		//TODO Later revise it
		//this.$el.parent().draggable();
		//self.isDragging = false;

  		$.extend(this.events,{
			//'dragstart':function(e){
             //   //Set flag for when click disable when click
			//	self.isDragging = true;
			//},
  			'click': function(e){
                //if (self.isDragging) {
                //    self.isDragging = false;
                //    e.preventDefault();
                //}
                //When click close facet remove
				if ($(e.target).is('.oe_facet_remove')) {
                            this.model.destroy();
                            this.$el.focus();
                            return false;
                        }
                //When click to facet value
                else if ($.inArray('oe_facet_value', e.target.classList) >= 0) {
                        var search_value = e.target.textContent.trim();
                        //When facevalue > more than 1 item
                        if (this.$el.find('.oe_facet_value').length > 1) {
                            e.target.remove();
                            //remove a clicked facet value
                            this.model.values.models = this.model.values.models.filter(function (item) {
                                return item.get('value') != search_value;
                            });
                            //Refresh search
                            this.__parentedParent.do_search();
                        }
                        else
                            this.model.destroy();
                        $('.oe_searchview_input:last-child').focus().text(search_value);
                    }
  			},
  		});
  	},

  });

  /**
   * Cho phep dinh nghia so luong ban ghi su dung o dropdown list trong
   * truong many2one: options="{'limit':8}"
   * TODO: bo sung them cac options khac
   */
  session.web.form.CompletionFieldMixin = _.extend(session.web.form.CompletionFieldMixin,{
  	init: function(){
  		if (typeof this.options.limit ==='number'){
  			this.limit = this.options.limit;
  		} else {
  			this.limit = 7;
  			}
        this.orderer = new session.web.DropMisordered();
  	}
  })


   /**
   * Trinh bay phan custom search list de chi show ra khi click vao Custom Filters
   * Khi co qua nhieu custom search list se lam roi search drawer
   * toggleClass(class,false/true) tuong duong tat/bat
   */
  session.web.search.CustomFilters = session.web.search.CustomFilters.extend({
  	start: function(){
  		var self = this;
		this._super();
		$('.openerp .oe_searchview_custom_list').hide();
		$('.openerp .oe_searchview_custom_saved_list h3').on('click',function(){
			if ($('.openerp .oe_searchview_custom_list li').length > 0) {
				$('.openerp .oe_searchview_custom_list').toggle();
			}
		});
  	},

  	show_custom_filters: function(){
  		$('.openerp .oe_searchview_custom_list').toggle();
  	},

  	append_filter: function(filter){
  		var self = this;
  		this._super(filter);
		$('.openerp .oe_searchview_custom_list li').on('click',function(){
			$('.oe_searchview').toggleClass('oe_searchview_open_drawer',false);
		});
  	},

  })

	/**
	 * Bo sung dieu kien like phuc vu cho
	 * trinh bay xml: attrs=
	 * Ke thua ham, sua dieu kien cua arguments,
	 * arguments: la dang mang [array1, object]: array1 la domain, object la danh sach cac truong va gia tri
	 * Tim dieu kien trong domain, neu co tu indexOf thi se kiem tra dieu kien theo ham Index
	 * Kq la True: tra ve dieu kien code!=false (dieu kien luon dung),
	 * Kq la False: tra ve dieu kien code=false (dieu kien luon sai),
	 * TODO: ke thua ham chua lam
	 */
  	var old_compute_domain = session.web.form.compute_domain; //Link compute_domain
  	session.web.form.compute_domain = function() {
	var tmp=$.extend(true,[],arguments);//Clone Object Arguments
	if (tmp[0][0])
		{
		var vdomain=tmp[0][0];
		if (typeof vdomain=='object')//Kiem tra domain phai la dang array khong phai la cac ky tu dac biet nhu '|', &, !
			if (vdomain[1].toLowerCase()==='indexof')
				{
					var field = tmp[1][vdomain[0]];
					var value = vdomain[2];
			        if (!field) {
			            throw new Error(_.str.sprintf(
			                _t("Unknown field %s in domain %s"),
			                value, JSON.stringify(value)));
			        }
			        var field_value = field.get_value ? field.get_value() : field.value;
			        tmp[0][0][2]='false'
			        if (!field_value)
			        	tmp[0][0][1]='='
			        else
    				        if (field_value.toLowerCase().indexOf(value.toLowerCase())>=0)
    				        	tmp[0][0][1]='!='
    				        else
    				        	tmp[0][0][1]='='
				}
		};
		var result = old_compute_domain.apply(this, tmp);
		return result;
  	};
};//For Learning
//on_menu_settings: function() {
//    var self = this;
//    if (!this.getParent().has_uncommitted_changes()) {
//        self.rpc("/web/action/load", { action_id: "base.action_res_users_my" }).done(function(result) {
//            result.res_id = instance.session.uid;
//            self.getParent().action_manager.do_action(result);
//        });
//    }
//},
openerp.kderp_web = function(session) {
    var _t = session.web._t;
    var QWeb = session.web.qweb;
    var has_action_id = false;
    var editmode_attachement=false;
    var unlinkable=false;
    var _lt = session.web._lt;
    //For Sort field in sidebar
    var vsort_by_field_att='label';
    //For string in Search
    var less_than_str = _t("Less Than ");
    var greater_than_str = _t("Greater Than ");

    session.web.form.widgets.add('many2oneimage','session.web.form.FieldMany2OneImage');

    //Change link favicon
    $('link[href="/web/static/src/img/favicon.ico"]').attr('href','/kderp_web/static/src/img/favicon.ico');
    (function() {
        var link = document.createElement('link');
        link.type = 'image/x-icon';
        link.rel = 'shortcut icon';
        link.href = '/kderp_web/static/src/img/favicon.ico';
        document.getElementsByTagName('head')[0].appendChild(link);
    }());

    //Move to Top Page
    var move_top_page = function (move)
    		{
    			move = typeof move !== 'undefined' ? move : true;
    			//Check top or not
    			if (move)
    				{
	    			var $win = $(window);
	    			if ($win.scrollTop() == 0)
	    				move=false;
    				}

    			if (move)
    				return $("html, body").animate({ scrollTop: 0},"fast")
    		};

//Function Attach Input mask
	var attach_mask_editable= function (obj,record) {
    			var normalize_format = function (format) {
    			    return Date.normalizeFormat(session.web.strip_raw_chars(format));
    			};
    			var l10n = _t.database.parameters;
    			var date_pattern = normalize_format(_t.database.parameters.date_format);

    			var excepted_list_fields=['due_date2'];

    			$.extend($.inputmask.defaults, {
    			    'clearMaskOnLostFocus': true
    			});
    			//Them Input Mask Pattern)
    			$.extend($.inputmask.defaults.aliases, {
    			'dd-mm-yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MM-yyyy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MMM-yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MM-yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd-MMM-yyyy': {
    		        mask: "1-2-y",
    		        placeholder: "dd-mm-yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    },
    		    'dd/mm/yy': {
    		        mask: "1-2-y",
    		        placeholder: "dd/mm/yyyy",
    		        leapday: "29-02-",
    		        separator: '-',
    		        alias: "dd/mm/yyyy"
    		    }});

    			obj.each( function( index, element ){
    				var main_elem=$( this );
    				elem=main_elem[0];

    				if (excepted_list_fields.indexOf(elem.name)<0)
    					{
    					if ( (typeof(elem.classList) !== 'undefined'))
    						if (elem.classList.contains('oe_datepicker_master') || check_parent(elem,'oe_datepicker_master'))
    								{
    								if (typeof(elem.value) !== 'undefined' && elem.value !== null && elem.value !== "")
    									{
    										try
    											{
    											get_date=elem.value;
    											if (typeof(record)==='object')
    												{
    													get_date=record[elem.name];
    													var date = Date.parseExact(get_date, 'yyyy-MM-dd');
    												}
    											else
    												var date = Date.parseExact(get_date, date_pattern);

    											if (date===null && typeof(elem.value)==='string')
    												date_value=elem.value;
    											else
    												date_value=date.toString(normalize_format(l10n.date_format).replace("MMM","M"));

    											elem.value=date_value;
    											}
    										catch (err)
    											{
    											console.log(elem.value);
    											console.log(date);
    											console.log(date_pattern);
    											console.log(elem.value);
    											}

    									}
    								input_mask=normalize_format(l10n.date_format).replace("MMM","mm");
    								main_elem.inputmask(input_mask);

    								main_elem.bind({
    									focusout :function() {
    									  	check_and_complete_date(this,input_mask,date_pattern);
    								  	},
    									hover: function() {
    									  	check_and_complete_date(this,input_mask,date_pattern);
    									  	},
//    									  blur: function() {
//    										  	check_and_complete_date(this,input_mask,date_pattern);
//    										  	},
    									});
    							}
    						else
    							if (check_parent(elem,'oe_form_field_float'))
    								{
    									if (check_parent(elem,'spinner'))
    										{

    										$( elem).spinner();
    										$(elem).addClass('oe_form_field_float');
    										main_elem.inputmask('decimal', { rightAlignNumerics: false, groupSeparator: ',', autoGroup: true });
    										}
    									else
    										main_elem.inputmask('decimal', { rightAlignNumerics: false, groupSeparator: ',', autoGroup: true });
    								}
    					}

    			});
    		};

//    var old_func=session.web.fields_view_get;
//    session.web.fields_view_get = function (args) {
//    	console.log(args);
//    	console.log("ARGS");
//    	return old_func(args);
//    };

    session.web.DataSetSearch = session.web.DataSetSearch.extend({
    	read_slice: function (fields, options) {
    		var _super=this._super(fields,options);
    		return $.when(_super,move_top_page($(".ui-dialog-content").length<=0));
    	}
    });
    //End of Move to Top Page

    /* Extend the Sidebar to add Share and Embed links in the 'More' menu */
    session.web.Sidebar.include({
    	sort_sidebar: function () {
    		var obj=this;
    		var vsort_by_field='label';
            var sort_by = function(field, reverse, primer){
            	   var key = primer ?
            	       function(x) {return primer(x[field])}:
            	       function(x) {return x[field]};

            	   reverse = [-1, 1][+!!reverse];

            	   return function (a, b) {

            	       return a = key(a), b = key(b), reverse * ((a > b) - (b > a));
            	     }
            	};

            for (section_code in obj.items)
            	{
	            	if (section_code==='other')
	            		{
		            		obj.items[section_code].forEach(function (value)
		            				{
		            				special_char=String.fromCharCode(255);
		            				if (value.label==='Duplicate')
		            					value.sort_label=special_char+'00';
		            				else if (value.label==='Delete')
		            					value.sort_label=special_char+'05';
		            				else if (value.label==='Export')
		            					value.sort_label=special_char+'10';
		            				else if (value.label==='View Log')
		            					value.sort_label=special_char+'15';
		            				else
		            					value.sort_label=value.label;
		            				});
		            	obj.items[section_code].sort(sort_by('sort_label', true, function(a){return a.toUpperCase()}));
	            		}
	            	else if (section_code==='files')
	            		{
        				obj.items[section_code].sort(sort_by(vsort_by_field_att, true, function(a){return a;}));
	            		}
	            	else
	            		{
	            		obj.items[section_code].sort(sort_by(vsort_by_field, true, function(a){return a.toUpperCase()}));
	            		}
            	}
        },

    	redraw: function() {
            var _super=this._super(this);
            var self =this;
            return $.when(_super).done(self.sort_sidebar());
        },

        on_attachments_loaded: function(attachments) {
		      var self = this;
		      var _super=self._super(attachments);
		      return $.when(this._super(attachments)).done(self.sort_sidebar());
        	},

    });

    //Hide Delete Attachment in some Model
    session.web.Sidebar = session.web.Sidebar.extend({

        start: function() {
        	new session.web.Model("ir.attachment").get_func("has_gorup_hidden")(session.uid).pipe(function(result) {
        		editmode_attachement=result;});

        	new session.web.Model("ir.attachment").get_func("check_location")(session.uid).pipe(function(result) {
    			if (result!=='hcm')
    				{
    				vsort_by_field_att='create_date';
    				}
    			else
    				vsort_by_field_att='label';
    			});

            var self = this;
            var _super=this._super(this);
            this.exept_model=['sale.order','purchase.order','account.invoice','kderp.contract.client'];
            this.editmode_attachement=editmode_attachement;

            self.add_items('other', [
                {   label: _t('View Log'),
                    callback: self.on_click_view_log,
                    classname: 'oe_share' },
            ]);
            return _super;
        },

        on_click_view_log: function(item) {
        	self=this;
            var view = this.getParent();
            this.dataset = view.dataset;
            var ids = view.get_selected_ids();

            if (ids.length === 1) {
                this.dataset.call('perm_read', [ids]).done(function(result) {
                    var dialog = new session.web.Dialog(this, {
                        title: _.str.sprintf(_t("View Log (%s)"), self.dataset.model),
                        width: 400
                    }, QWeb.render('ViewManagerDebugViewLog', {
                        perm : result[0],
                        format : session.web.format_value
                    })).open();
                });
            }

        },

    });

//Check date and number
var check_and_complete_date = function (obj,input_mask,date_pattern) {
		var date_string=obj.value;

		var date_separate="";
//		console.log("OBJ:");
//		console.log(this);
//		console.log("Input");
//		console.log($("input[name='"+ obj.name + "']"));
		if (date_string.indexOf("-")>=0)
			{date_separate='-';}
		else if (date_string.indexOf("/")>=0)
			{date_separate='/';}
		else if (date_string.indexOf(".")>=0)
			{date_separate='.';}

		if (date_separate !=="")
			{
				date_array=date_string.split(date_separate);

				first=parseInt(date_array[0]);
				first=("0" + first).slice(-2);

				second=date_array[1];
				second=parseInt(second);
				update=false;

				if (isNaN(second))
					{
						//date_array_pattern=input_mask.split(date_separate);
						var curr_date = new Date();
						var curr_date_str = curr_date.toString(date_pattern.replace("MM","M"));
						second=curr_date_str.split(date_separate)[1]
						second=("0" + second).slice(-2);
						third=curr_date_str.split(date_separate)[2]
						update=true
					}
				else
					{
						third=date_array[2];
						third=parseInt(third);
						second=("0" + second).slice(-2);

						if (isNaN(third))
							{
								var curr_date = new Date();
								var curr_date_str = curr_date.toString(date_pattern.replace("MM","M"));
								third=curr_date_str.split(date_separate)[2]
								update=true
							}
						else
							{
								str_third=third.toString();
								if (str_third.length<4)
									{
										third="1"+parseInt(str_third[str_third.length-1]);
										update=true
									}
							}
					}
				if (update && !isNaN(first))
					{
					date_value=first + date_separate + second + date_separate + third;

					$(obj).val(date_value)
													.change();


					}
			}
};

var check_parent = function (obj,name_class)
	{
		var result=false;
		if (typeof(obj.parentNode) !== 'undefined')
			if (typeof(obj.parentNode.classList) !== 'undefined')
				if (obj.parentNode.classList.contains(name_class))
					result=true;
		return result;
	}



//Change return value when click to Picker date
session.web.DateWidget = session.web.DateWidget.extend ({
    on_picker_select: function(text, instance_) {
        var date = this.picker('getDate');
        this.$input
            .val(date ? this.kderp_format_client(date) : '')
            .change()
            .focus();
    },
	kderp_format_client: function(v) {
		var normalize_format = function (format) {
		    return Date.normalizeFormat(session.web.strip_raw_chars(format));
		};
    	var l10n = _t.database.parameters;
    	date_value=v.toString(normalize_format(l10n.date_format).replace("MMM","M"));
        return date_value;
    },
});

////Add InputMask for tree editable
//session.web.list.Editor= session.web.list.Editor.extend({
//    _focus_setup: function (focus_field) {
//    	 _super = this._super(focus_field);
//    	 var self=this;
//		return _super;
//    	// return $.when(_super,attach_mask_editable(self.$el.find('input'),this.record));
//    },
//
//});

//session.web.ViewManagerAction = session.web.ViewManagerAction.extend({
//
//    do_create_view: function(view_type) {
//        var self = this;
//        return this.alive(this._super.apply(this, arguments)).done(function() {
//        	if (view_type==='form')
//        		{
//					return true;
//        		setTimeout(function (){
//        				attach_mask_editable($(self.$el.find('div.oe_form')[0]).find('input[type=text]'));
//        				},500);
//        		}
//        });
//    },
//});

session.web.FormView =  session.web.FormView.extend({

	check_actual_mode: function(source, options) {
        var self = this;
        var _super=this._super(source, options);
        var showSideBar = function ()
        	{
	        	if (self.get("actual_mode") !== "view" && self.datarecord.id)
	        		self.$sidebar.show();
        	}
        return $.when(_super,showSideBar());
    },

	load_form: function(data)
		{
		var self=this;
		var objj=this;

        // DBClick to Edit mode
		var bind_event= function(evt){
				objj.$el.find(".oe_form_group_row,.oe_form_field,label").on('dblclick', function (e) {
		            if(self.get("actual_mode") === "view") {
		            	self.options.$buttons.find(".oe_form_button_edit").click();
		            	e.preventDefault();
		            }
		        });
				$(document).on('keydown',function (e) {
					if ($(".ui-dialog-content").length<=0 && ($(':focus').length===0) && e.which === 69 && self.get("actual_mode") === "view") //e.ctrlKey && !e.altKey && !e.shiftKey
						{
						//console.log($(':focus').parent());
						self.options.$buttons.find(".oe_form_button_edit").click();
						e.preventDefault();
						}
					else if (e.ctrlKey && !e.altKey && !e.shiftKey && e.which === 68) //Duplicate when Ctrl+D
						{
							e.preventDefault();
//							console.log(self.options.$sidebar);
							//return self.guard_active(self.on_button_duplicate(self));
						}
					else if(e.ctrlKey && !e.altKey && !e.shiftKey && e.which === 83) // Check for the Ctrl key being pressed, and if the key = [S] (83)
						if(self.get("actual_mode") === "edit")
							{
							e.preventDefault();
							var save_mode=self.options.$buttons.find(".oe_form_button_save").click();
							setTimeout(function(){
								$('<div>')
							      .attr('class', 'kderp_oe_notification')
							      .html("<div class='.openerp .kderp_oe_notification'></div>")
							      .fadeIn('fast')
							      .insertAfter($('.oe_loading'))  //<== wherever you want it to show
							      .animate({opacity: 1.0}, 1000)     //<== wait 3 sec before fading out
							      .fadeOut('slow', function()
							      {
							        $(this).remove();
							      });
									self.options.$buttons.find(".oe_form_button_edit").click();
									},500);
							}
		        });
				//Always in Edit Mode
				if(self.get("actual_mode") === "view") {
					setTimeout(function(){return self.options.$buttons.find(".oe_form_button_edit").click();},500);
		        }
		};

		var _super=this._super(data);
		return $.when(_super,bind_event())
	}
    });

/*
 * Sua phan xoa line o trong List many2one
 * Bi loi khi nhap budget, do list view se cap nhat du lieu theo tu tu sua, vi vay khi them 1 dong vao roi xoa 1 dong
 * Khi commit ma co rang buoc trung du lieu thi se bao loi do co 2 ban ghi trung nhay
 * Sua lai de cho phan xoa len tren cung
 * */
session.web.DataSet.include({
	write: function (id, data, options) {
		 _.each(data, function (dat) {
             if (dat instanceof Object)
                     dat.sort(function (rd) {
                             switch(rd) {
                                     case 2: return 0
                                     case 3: return 1
                                     case 1: return 2
                                     case 0: return 3
                                     case 4: return 4
                                     }
                             return 5

                     })});
		 return this._super(id, data, options);
	},
});

session.web.search.InputView = session.web.search.InputView.extend({
    //init: function (parent, model) {
    //    this._super(parent,model);
		//this.$el.draggable();
		//console.log(this);
    //},
	onKeydown: function (e) {
		var _super=this._super(e);
		   switch (e.which) {
	        case $.ui.keyCode.ESC:
	        	e.preventDefault();
	        	preceding.model.destroy();
	            break;
		   }
		return _super;
	}

});

/**
 * start
 * An cua so search khi di roi con tro chuot
 * Su dung timer de cancel event khi su kien xay ra lien tiep trong khoang thoi gian delay
 * vi du: di chuyen chuot lien tuc vao va ra khoi element
 * De cho o search co the drag duoc
 *
 * select_completion
 * Dinh dang cach hien thi Ngay va So khi go o phan search. Them phan tim kiem theo khoang, tim kiem not o phan search
 * setup_global_completion
 * Dieu chinh phan delay cua search tu 250 xuong 0 -- more responsive
 * TODO
 *
 * build_search_data
 * Them dieu kien search hoac (or) cho cac filter da co san
 * Kiem tra dieu kien search nhap vao neu co chua || thi se them vao domain search
 * dieu kien hoac
 */

session.web.SearchView = session.web.SearchView.extend(/** @lends instance.web.SearchView# */{
    start: function () {
        var self = this;
        this._super(this);
		this.$el.draggable({containment: this.$el.parents('.oe_header_row')});

        time_to_leave = 2500;
        var timer;
        this.$el.find('.oe_searchview_drawer').on('mouseleave', function(){
        	timer = setTimeout(function(){
        		self.$el.toggleClass('oe_searchview_open_drawer', false);
        	},1000)
        });
        this.$el.find('.oe_searchview_drawer').on('mouseenter', function(){
        	clearTimeout(timer);
        });
    },

	select_completion: function (e, ui) {
		var filter_value=ui.item.facet.values[0].actual_value;

		var type_value='string';

		if (typeof(filter_value) === 'undefined')
			{
			filter_value=ui.item.facet.values[0].value;
			}
		else if (typeof(filter_value) === 'object')
			{
			var type_filter = filter_value.value_type;
			//Date Area
			if (type_filter==='range_date')
				{
					var from_string=filter_value.date.toString('dd-MMM-yyyy');
					var to_string=filter_value.to_date.toString('dd-MMM-yyyy');
					var string_label="Range :" + from_string+"~"+to_string;

					filter_value=filter_value.date.toString('yyyy-MM-dd')+"~"+filter_value.to_date.toString('yyyy-MM-dd');
					type_value='date';
				}
			else if (type_filter==='greater_date')
				{
				var from_string=filter_value.date.toString('dd-MMM-yyyy');
				var string_label=greater_than_str + from_string;

				filter_value=filter_value.date.toString('yyyy-MM-dd')+"~";
				type_value='date';
				}
			else if (type_filter==='less_date')
				{
				var to_string=filter_value.to_date.toString('dd-MMM-yyyy');
				var string_label=less_than_str + to_string;

				filter_value="~"+filter_value.to_date.toString('yyyy-MM-dd');
				type_value='date';
				}
			//Number Area
			else if (filter_value.type==='number')
				{
					type_value='number';
					if (type_filter==='greater_number')
						{
							filter_value=filter_value.from_number.toString()  + "~";
						}
					else if (type_filter==='less_number')
						{
							filter_value="~" + filter_value.to_number.toString();
						}
					else
						{
							filter_value=filter_value.from_number.toString() + "~" + filter_value.to_number.toString();
						}
				}
			}

		var original_value=filter_value;
		var filter_domain="";

		ui.item.facet.field.view.fields_view.arch.children.forEach(function (value) {
			if (ui.item.facet.field.attrs['string'] === value.attrs.string && ui.item.facet.field.attrs['name'] === value.attrs.name)
				{
				filter_domain=value.attrs.filter_domain;
				}
		});

		if (typeof(filter_value)==='string')
			{
				var prefix="";
				filter_value=filter_value.toUpperCase();
				if (filter_value.search(/\\/)>0 && filter_value.search("~")>2)
		    		{
			    		prefix=filter_value.split(/\\(.+)?/)[0];
			    		range=filter_value.split(/\\(.+)?/)[1];

			    		from_value=range.split("~")[0]
			    		to_value=range.split("~")[1]

			    		from_value=prefix.trim()+from_value
			    		to_value=prefix.trim()+to_value

			    		filter_value="\\" + from_value + "~" + to_value;

		    		}
				if (['date','number'].indexOf(type_value)>=0 && filter_value.search("~")>=0)
					{

					//prefix1=filter_value.split("\\")[0];
		    		range_value=filter_value;

		    		from_value=range_value.split("~")[0]
		    		to_value=range_value.split("~")[1]

		    		field_name=ui.item.facet.field.attrs['name'];
		    		if (type_value==='number')
		    			{
		    			if (type_filter==='greater_number')
		    				{
			    				filter_domain="[('" + field_name +"','>=',"+from_value+")]";
				    			//filter_domain=filter_domain+",('" + field_name +"','<=',"+to_value+")]";
		    				}
		    			else if (type_filter==='less_number')
		    				{
			    				//filter_domain="[('" + field_name +"','>=',"+from_value+")";
				    			filter_domain="[('" + field_name +"','<=',"+to_value+")]";
		    				}
		    			else
		    				{
			    				filter_domain="[('" + field_name +"','>=',"+from_value+")";
				    			filter_domain=filter_domain+",('" + field_name +"','<=',"+to_value+")]";
		    				}
		    			}
		    		else if (type_filter==='greater_date')
		    			{
			    			filter_domain="[('" + field_name +"','>=','"+from_value+"')]";
	//		    			filter_domain=filter_domain+",('" + field_name +"','<=','"+to_value+"')]";
		    			}
		    		else if (type_filter==='less_date')
	    				{
			    			//filter_domain="[('" + field_name +"','>=','"+from_value+"')";
			    			filter_domain="[('" + field_name +"','<=','"+to_value+"')]";
	    				}
		    		else
	    				{
			    			filter_domain="[('" + field_name +"','>=','"+from_value+"')";
			    			filter_domain=filter_domain+",('" + field_name +"','<=','"+to_value+"')]";
	    				}
					//ui.item.facet.field.attrs.filter_domain=filter_domain;

					ui.item.facet.category= ui.item.facet.category + new Date().getTime();

					//ui.item.facet.field.attrs.filter_domain=filter_domain;
					//filter_value = filter_value.replace("!!", "");
					ui.item.facet.values[0].value = original_value;
					//ui.item.facet.filter_domain=filter_domain;
					if (typeof(string_label)==='undefined')
						{
						ui.item.facet.values[0].label = "Range :" + from_value + "~" + to_value;
						}
					else
						{
						ui.item.facet.values[0].label=string_label;
						}

					}
				else if (filter_value.search(/\\/)===0 && filter_value.search("~")>2)
						{
							prefix1=filter_value.split(/\\/)[0];
				    		range_value=filter_value.split(/\\/)[1];

				    		from_value=range_value.split("~")[0]
				    		to_value=range_value.split("~")[1]

				    		field_name=ui.item.facet.field.attrs['name'];
				    		if (type_value==='number')
				    			{
				    			filter_domain="[('" + field_name +"','>=',"+from_value+")";
				    			filter_domain=filter_domain+",('" + field_name +"','<=',"+to_value+")]";
				    			}
				    		else
				    			{
				    			filter_domain="[('" + field_name +"','>=','"+from_value+"')";
				    			filter_domain=filter_domain+",('" + field_name +"','<=','"+to_value+"')]";
				    			}
							//ui.item.facet.field.attrs.filter_domain=filter_domain;

							ui.item.facet.category= ui.item.facet.category + new Date().getTime();

							//ui.item.facet.field.attrs.filter_domain=filter_domain;
							//filter_value = filter_value.replace("!!", "");
							ui.item.facet.values[0].value = original_value;
							//ui.item.facet.filter_domain=filter_domain;
							if (typeof(string_label)==='undefined')
								{
								ui.item.facet.values[0].label = "Range :" + from_value + "~" + to_value;
								}
							else
								{
								ui.item.facet.values[0].label=string_label;
								}
						}
				//Search NOT

		        if (filter_value.search("!!")===0 && typeof(filter_domain)!=='undefined' && typeof(filter_domain)==="string")
		        	{
		        		var find_replace_condition = function (filter_domain, vFind, vRplace)
		        		{
			        		tmp_filter_domain=filter_domain.split(vfind);
			        		for (var i=0; i < tmp_filter_domain.length; i++)
			        		    {
			        				tmp_filter_domain[i].split(vReplace).join(vFind);
			        		    }
		        			return tmp_filter_domain.join(vRplace);
		        		};

			        	ui.item.facet.category= ui.item.facet.category + new Date().getTime();

			        	filter_domain=filter_domain.split(", ").join(",");
			        	filter_domain=filter_domain.split(" ,").join(",");
			        	vfind=",'=',";
			        	vReplace=",'!=',";
			        	filter_domain=find_replace_condition(filter_domain,vfind,vReplace);

			        	vfind=",'ilike',"
			        	vReplace=",'not ilike',"
			        		filter_domain=find_replace_condition(filter_domain,vfind,vReplace);

			        	vfind=",'in',"
			        	vReplace=",'not in',"
		        		filter_domain=find_replace_condition(filter_domain,vfind,vReplace);
			        	 if (filter_value.indexOf("!!")===0)
			        		{
								filter_value = filter_value.replace("!!", "");
								ui.item.facet.values[0].value=filter_value;
								ui.item.facet.values[0].label="!" +filter_value;
			        		}
		        	}
			}
		ui.item.facet.filter_domain=filter_domain;
        ui.item.facet.field.attrs.filter_domain=filter_domain;
        //console.log(filter_domain);
        var _super=this._super(e,ui);
        return _super;
    },

    setup_global_completion: function(){
    	this._super();
        var autocomplete = this.$el.autocomplete({
            source: this.proxy('complete_global_search'),
            select: this.proxy('select_completion'),
            focus: function (e) { e.preventDefault(); },
            html: true,
            autoFocus: true,
            minLength: 1,
            delay: 0, //original value is 250
        }).data('autocomplete');
    },

	build_search_data: function () {
            var _super = this._super();
            var domains = _super.domains;

            if (domains.length>=1)
				{
					//Chuyen domain thanh string
					convertDomaintoString = function(domain) {
						if (domain.eval === undefined)
							if ($.type(domain) === 'string')
								return domain;
							else
								return JSON.stringify(domain);
						else
							return JSON.stringify(domain.eval());
					};
					var searchDomain = convertDomaintoString(domains[domains.length-1]);

                if (searchDomain.indexOf('"||')>=0 || searchDomain.indexOf("'||")>=0) {
                    searchDomain = searchDomain.replace(/\'\|\|/g,"'").replace(/\"\|\|/g,'"');

                    sDomain0 = convertDomaintoString(domains[0]);
					sDomain0 = py.eval(sDomain0);
					sDomain1 = py.eval(searchDomain);

					pos = sDomain0.indexOf('|');
                    if (pos < 0)
                        sDomain0.splice(sDomain0.length - 1, 0, '|');
                    else
                        sDomain0.splice(pos, 0, '|');
                    sDomain0 = sDomain0.concat(sDomain1);
					//console.log(sDomain0);
                    domains.pop();
                    domains[0] = JSON.stringify(sDomain0);

                }
			}
			return _super;
        },
    });


//Chuyen domain cua tung facet vao search
session.web.search.Field.include({

    get_domain: function (facet) {
    	this.attrs['filter_domain']=facet.attributes['filter_domain'];
        return this._super(facet);
    }
});

//Show Number Field if match Pattern
session.web.search.NumberField = session.web.search.NumberField.include(/** @lends instance.web.search.NumberField# */{
    complete: function (needle) {

        var range=_t("");
        if (typeof(needle)==='string')
    		if (needle.search("~")>=0)
    	    			{
    	    			from_amount=needle.split('~')[0].split(" ").join("").split(",").join("")
    	    			to_amount=needle.split('~')[1].split(" ").join("").split(",").join("")
    	    			var val = this.parse(from_amount);
    	    			var tval = this.parse(to_amount);

    	    			if (val && tval) //Neu co ca a~b
    	    				{
    	    					range=_t("Range ");
    	    					var return_value={'value_type':'number','type':'number','from_number':val,'to_number':tval};
    	    					var number_string= range + ":" + val.toLocaleString() + "~" + tval.toLocaleString();
    	    				}
    	    			else if (val) //Neu co ca a~
    	    				{
	    	    				var return_value={'value_type':'greater_number','type':'number','from_number':val,'to_number':tval};
		    					var number_string= greater_than_str + val.toLocaleString();
    	    				}
    	    			else if (tval) //Neu co ca ~b
    	    				{
	    	    				var return_value={'value_type':'less_number','type':'number','from_number':val,'to_number':tval};
		    					var number_string= less_than_str + tval.toLocaleString();
    	    				}
    	    			else
    	    				val = undefined
    	    			}
	    		else
	    			{
	    			var val = this.parse(needle.split(" ").join("").split(",").join(""));
	    			var number_string= val.toLocaleString();
	    			}
    	else
    		{
	    		var val = this.parse(needle.split(" ").join("").split(",").join(""));
	    		var number_string= val.toLocaleString();
    		}

        if (isNaN(val)) { return $.when(); }
        var label = _.str.sprintf(
            _t("Search %(range)s%(field)s for: %(value)s"), {
            	range: range,
                field: '<em>' + this.attrs.string + '</em>',
                value: '<strong>' + number_string  + '</strong>'});
        return $.when([{
            label: label,
            facet: {
                category: this.attrs.string,
                field: this,
                values: [{label: number_string, value: val, actual_value:return_value}]
            }
        }]);
    },
});

//Show Date Field if match Pattern
session.web.search.DateField = session.web.search.DateField.extend(/** @lends instance.web.search.DateField# */{
    value_from: function (facetValue) {
    	if (typeof(facetValue.get('value'))==='string')
    		return true;
    	else
    		return this._super(facetValue);
    },
    complete: function (needle) {
    	var check_date=false;
    	var range="";

    	if (typeof(needle)==='string')
    		if (needle.search("~")>=0)
    			{
    			//needle=needle.split('\\')[1];
    			from_date=needle.split('~')[0]
    			to_date=needle.split('~')[1]
    			var d = Date.parse(from_date);
    			var td = Date.parse(to_date);

    			if (td && d)
    				{
    				check_date=true;
    				var range=_t("Range ");
    				var return_value={'value_type':'range_date','type':'range_date','date':d,'to_date':td};
    				var date_string = d.toString("dd-MMM-yyyy") + "~" + td.toString("dd-MMM-yyyy")
    				}
    			else if (d) //Greater Than
    				{
    				check_date=true;
    				var range=_t("");
    				var return_value={'value_type':'greater_date','type':'range_date','date':d};
    				var date_string = "Greater Than " + d.toString("dd-MMM-yyyy")
    				}
    			else if (td) //Less Than
    				{
    				var range=_t("");
    				check_date=true;
    				var return_value={'value_type':'less_date','type':'range_date','to_date':td};
    				var date_string = "Less Than " + td.toString("dd-MMM-yyyy")
    				}
    			}
    		else
    			{
    			var d = Date.parse(needle);
    			if (d)
    				{check_date=true;
    				var date_string =  d.toString("dd-MMM-yyyy");
    				var return_value={'type':'date','date':d};
    				}
    			}
    	else
    		{
    			var d = Date.parse(needle);
    			if (d)
    				check_date=true;
    			var date_string =  d.toString("dd-MMM-yyyy");
    		}
    	if (!check_date) { return $.when(null); }
        var label = _.str.sprintf(_.str.escapeHTML(
            _t("Search %(range)s%(field)s at: %(value)s")), {
        		range: range,
                field: '<em>' + this.attrs.string + '</em>',
                value: '<strong>' + date_string + '</strong>'});
        return $.when([{
            label: label,
            facet: {
                category: this.attrs.string,
                field: this,
                values: [{label: date_string, value: d, actual_value:return_value}]
            }
        }]);
    }
});

//Open New Tab instead of PopUp
var open_new_tab = function (data,target,kd_context1)
	{
//		console.log('NEW');
		window.kd_context=kd_context1;
		var x_open = window.open(data['server']+"/?#id="+data['id']+"&view_type=form&model="+data['model'], target);
		return x_open;
	};

//session.web.form.SelectCreatePopup = session.web.form.SelectCreatePopu1p.extend({
//	new_object: function() {
// 		var self=this;
// 		return $.when(self._super()).then(function () {
//				return true;
// 				setTimeout(function(){
// 					attach_mask_editable($('div.ui-dialog-content.ui-widget-content').find("input[type='text']"));
// 				},500);
// 				});
// 	},
//});

//Click to Tree View
session.web.form.AbstractFormPopup1 = session.web.form.AbstractFormPopup.include({

	    display_popup: function() {
	    	var self=this;

	    	if (!(parseInt(this.row_id)>0 && this.options.target!=='new_popup' && ['kderp.supplier.vat.invoice','res.partner'].indexOf(self.model)<0 ))
	    		{
    			var no_return="";
    			var revalue= function (obj){
    				if (no_return!=="")
    					self.target=no_return;
    			};

	    		if (this.target==='new_popup')
	    			{
		    			this.target='new';
		    			no_return='new_popup';
	    			};
    			if (typeof(this.row_id)==='object' && this.row_id!==null)
    				{
    					this.row_id=this.row_id[0];
    				};
		    	return $.when(self._super(),revalue(this));
	    		}
	    	else
	    		{
		    		kd_context = session.web.pyeval.eval('context', this.context);
		    		window.kd_context=kd_context;
	    			window.open(this.session.server+"/?#id="+this.row_id+"&view_type=form&model="+this.model, '_blank');
	    			self.destroy();
	    		}
	    },
});

/**
 * Confirm before Delete a record in List View
 *
 * pad_table_to: bo sung de goi floating_header, delay 10ms
 *
 * floating_header: JQuery su dung de tao floating header cho tree view
 * header cua 1 bang se co dinh, khong bi cuon theo mouse
 * Bo sung them viec tinh toan lai header khi co gian man hinh
 */
session.web.ListView.List.include({
	init: function (group, opts) {
		this._super(group, opts);
		var self=this;
		this.$current.undelegate('td.oe_list_record_delete button', 'click');
		this.$current.delegate('td.oe_list_record_delete button', 'click', function (e) {
		         e.stopPropagation();
		         var $row = $(e.target).closest('tr');
		         if (self.row_id($row))
			         if (!confirm(_t("Do you really want to remove these records?"))) {
			        	 	return;
			         };
		         $(self).trigger('deleted', [[self.row_id($row)]]);
		     });
	     $(window).resize(function(){
	     	self.floating_header(self);
	     });
		},

	pad_table_to: function(count){
		this._super(count);
		var self = this;
		setTimeout(function(){
			self.floating_header(self);
		},0);

	},

//	render: function () {
//		var _super=this._super();
//		var self = this;
//		setTimeout(function(){
//			self.floating_header(self);
//		},10);
//	},

	floating_header: function(current_list){
		//Freezing table header in tree view
		//Clone headers
		if ($(".floatingHeader").length >0){ //Kiem tra floatingHeader co ton tai?
			$(".floatingHeader").remove()
			};

		if (current_list.options.search_view){
			//Kiem tra xem co phai la Tree view hay khong: co search view hay khong
			//su dung first de han che ap dung cho element dau tien, su dung clone(true) de copy event
			var $floatingHeader = $(".oe_list_header_columns").filter(":first").clone(true);
			    $floatingHeader.children().width(function (i, val) {
			    	return $(".oe_list_header_columns").filter(":first").children().eq(i).width();
			    });

		    	$floatingHeader.css({"width":$(".oe_list_header_columns").filter(":first").width()
		    		, "height":$(".oe_list_header_columns").filter(":first").height()})
		    		.addClass("floatingHeader");

		    	//$floatingHeader.css({"width", $(".oe_list_header_columns").filter(":first").width());
			    //$floatingHeader.css("height",$(".oe_list_header_columns").filter(":first").height()).addClass("floatingHeader");
			    $(".oe_list_header_columns").filter(":first").before($floatingHeader);
		};
	  },
});

/*
//Lost focus khong bi mat gia tri
session.web.form.One2ManyListView = session.web.form.One2ManyListView.extend({
	_on_form_blur: function () {
		this.__ignore_blur = true;
		return this._super();
    },
});
*/

//Keep checked when click Action
session.web.ListView.include({
	reload_content: function () {
		 var self=this;
		 var selected_ids=[];
		 var checked_all=self.$el.find('.oe_list_record_selector ').prop('checked');
		 var list_input_selected=this.$el.find('th.oe_list_record_selector input:checked').closest('tr').each(function () {
			 selected_ids.push($(this).data('id'));
		 	});
		 var _super=self._super(this);

		 return $.when(_super).done( function () {
			 	list_element_must_be_Check=[];
			 	$('th.oe_list_record_selector input').closest('tr').each(function (){
			 		if (selected_ids.indexOf($(this).data('id'))>=0)
			 			{
			 			list_element_must_be_Check.push($(this).find('input')[0]);
			 			};
			 	});
			 	self.$el.find('.oe_list_record_selector ').prop('checked',checked_all);
			 	$(list_element_must_be_Check).prop('checked',true);

			 });
	 },
});

	//Windows Action
//Pass context to Window.open
session.web.ActionManager = session.web.ActionManager.extend({

	init: function(parent) {
		var self=this;
		var _super=self._super.apply(self, arguments);
		try
			{
			if (typeof(window.opener.kd_context)!=='undefined')
				{
				if (typeof(window.opener.kd_context.executor)!=='undefined')
					{
					parent.session.user_context=window.opener.kd_context['executor'].action.context;
					}
				else
					{
					parent.session.user_context=window.opener.kd_context;
					};
				window.opener.kd_context={};
				}
			}
		catch (e)
			{
				console.log(e);//Hien thong bao loi
				return ;
				parent.session.user_context={};
			}
		return _super;
	},
//IR Windows Action with target new
	ir_actions_common: function(executor, options) {
		var tmp_action=executor.action;
		var self=this;
		if (tmp_action.tag==="change_password")
			{
				tmp_action.target='new_popup';
				var a= new session.web.ChangePassword(this);
				a.start();
			}
		if (tmp_action.res_model!='res.partner' && tmp_action.type==='ir.actions.act_window' && tmp_action.target=='new' && parseInt(tmp_action.res_id)>0)
			{
				new_tab_server = window.location.protocol+"//"+window.location.host;
				new_tab_data={'id':tmp_action.res_id,'model':tmp_action.res_model,'server':new_tab_server};
				open_new_tab(new_tab_data, '_blank',{'executor':executor,'options':options});
				return false;

			}
		else
			{
				if (tmp_action.target==='new_popup')
					executor.action.target='new';
				//var _super=self._super(executor, options);
				var _super=self._super.apply(self, arguments);
				return _super;
			}
	},
	});

/**
 * Backspace remove all
 *
 * this.$input.autocompete() ke thua ham nay de sua loi delay trong khi nhap
 * lieu o form voi cac truong Many2One doi delay: 0
 * Muon cho code gon hon nua TOD
 *
 * Luu y phan this._super(this) vs return this._super(this)
 */
session.web.form.FieldMany2One = session.web.form.FieldMany2One.extend({
	//display_string: function(str) {
	//	var res = this._super(str);
	//	var objM2O = this.$el.find('.oe_form_uri');
	//	var self = this;
	//	if (objM2O.length>0)
	//	{
	//		if (self.get("value")) {
	//			var ctx  = self.build_context();
	//			ctx.add({'show_title':1});
	//			var dataset = new session.web.DataSetStatic(this, this.field.relation, ctx);
	//			var def = this.alive(dataset.name_get([self.get("value")])).done(function (data) {
	//				if (!data[0]) {
	//					self.do_warn(_t("Render"), _t("No value found for the field " + self.field.string + " for value " + self.get("value")));
	//					return;
	//				}
	//			objM2O[0].title = data[0][1];
	//			});
	//		}
	//	}
	//	return res
	//},
	render_editable: function() {
        var self = this;
        this.$input = this.$el.find("input");
        this.$input.on('keydown',function (e) {
        	if (!e.ctrlKey && !e.altKey && !e.shiftKey && [8,46].indexOf(e.which)>=0 && self.get('value'))
        		{
        			e.preventDefault();
        			self.reinit_value(false);
        		}
        });
        this._super(this);

        this.$input.autocomplete({
            source: function(req, resp) {
                self.get_search_result(req.term).done(function(result) {
                    resp(result);
                });
            },
            select: function(event, ui) {
                isSelecting = true;
                var item = ui.item;
                if (item.id) {
                    self.display_value = {};
                    self.display_value["" + item.id] = item.name;
                    self.reinit_value(item.id);
                } else if (item.action) {
                    item.action();
                    // Cancel widget blurring, to avoid form blur event
                    self.trigger('focused');
                    return false;
                }
            },
            focus: function(e, ui) {
                e.preventDefault();
            },
            html: true,
            // disabled to solve a bug, but may cause others
            //close: anyoneLoosesFocus,
            minLength: 0,
            delay: 0
        });

//        return this._super(this);
	},
});

session.web.form.FieldMany2OneImage = session.web.form.FieldMany2One.extend({
	template: "FieldMany2OneImage",
	init: function(field_manager, node) {
		this._super(field_manager, node);
		this.vid=false;
	},
	/**
	 * Bat su kien hover len anh de phong to
	 * Su dung position: absolute de khi phong to khong anh huong den cac thanh phan khac
	 */
	events: {
		"mouseenter .koe_many2one_image": "img_enter",
		"mouseleave .koe_many2one_image": "img_leave"
	  },
	img_enter: function(){
		  this.$el.find(".koe_many2one_image").css({'width': '+=24px','height': 'auto','position':'absolute'});
	  },
	img_leave: function(){
		  this.$el.find(".koe_many2one_image").css({'width': '','height':'','position':'initial'});
	  },

	render_value: function(no_recurse) {
		var _super=this._super(no_recurse);
		var self=this;
		var url;
		field='image';
		self.vid=self.get("value");

		if (! no_recurse) {
			if (!self.get("value"))
				{
				self.$el.find('.koe_many2one_image').remove();
				}
            else
            	{
	            	var show_image = function (obj, model, vid, field)
	            		{
		            		dataset=new session.web.DataSetStatic(self, model, self.build_context());
		            		dataset.set_ids([vid]);
		            		obj.$el.find('.koe_many2one_image').remove();
		            		dataset.read_slice([field],{}).then(function (data){
		            				if (data.length>0)
		            					if (data[0][field])
		            						{
			            						url = self.session.url('/web/binary/image', {
			        		                        model: model,
			        		                        id: vid,
			        		                        field: field,
			        		                        t: (new Date().getTime()),
			        		                        });
			        			                var $img = $(QWeb.render("FieldBinaryImage-img", { widget: obj, url: url }));
			        			                obj.$el.find('.koe_many2one_image').remove();
			        			                $img.addClass('koe_many2one_image');
			        			                obj.$el.prepend($img);
			        			                $img.load(function() {
			        			                    if (! obj.options.size)
			        			                        return;
			        			                    $img.css("max-width", "" + self.options.size[0] + "px");
			        			                    $img.css("max-height", "" + self.options.size[1] + "px");
			        			                    $img.css("margin-left", "" + (self.options.size[0] - $img.width()) / 2 + "px");
			        			                    $img.css("margin-top", "" + (self.options.size[1] - $img.height()) / 2 + "px");
			        			                	});
		            						}
		            			});
	            		};

	            	if (self.options.preview_image)
	            		{
	            			var dataset = new session.web.DataSetStatic(self, self.field.relation, self.build_context());
		            		field_temp=self.options.preview_image;
		            		parent=field_temp.split('/')[0];
		            		field=field_temp.split('/')[1];
		            		if (typeof (field)!=='undefined')
		            			{
		            			dataset.set_ids([self.get("value")]);
		            			dataset.read_slice([parent],{}).then(function(data) {
		            				if (data.length>0)
		            					{
		            						if (self.options.model)
		            							show_image(self, self.options.model, data[0].employee_id[0], field);
		            						else
		            							show_image(self, dataset.model, data[0].employee_id[0], field);
		            					}
		                    		});
		            			}
		            		else
		            			{
		            			field=parent;
		            			if (self.options.model)
			            			show_image(self, self.options.model, self.vid, field);
		            			else
		            				show_image(self, self.field.model, self.vid, field);

		            			}
	            		}
	            	else
	            		{
	            		if (self.options.model)
	            			show_image(self, self.options.model, self.vid, field);
            			else
            				show_image(self, self.field.model, self.vid, field);
	            		}
            	};
		}

	return _super;
	},
});



/*
	Add inputmask to float field, Date
*/
session.web.form.FieldDate = session.web.form.FieldDate.extend({
	render_value: function() {
		var self = this;
		if (this.get("effective_readonly"))
			return this._super();
		else
			return $.when(this._super(),attach_mask_editable(self.$el.find('input')));
	},
});

session.web.form.FieldFloat = session.web.form.FieldFloat.extend({
	render_value: function() {
		var self = this;
		if (this.get("effective_readonly"))
			return this._super();
		else
			return $.when(this._super(),attach_mask_editable(self.$el.find('input')));
	},
});
//
//session.web.DateWidget = session.web.DateWidget.include({
//
//});

//Add widget as a progress bar on readyonly
//Extend for progressfloat - ke thua thiet ke cua progressbar
session.web.form.widgets.add ('progressfloat','session.web.form.progressfloat');
session.web.form.progressfloat = session.web.form.FieldFloat.extend({
	template: "FieldProgressBarFloat",
	render_value: function() {
		if (this.get("effective_readonly"))
			{
		        this.$el.progressbar({
		            value: this.get('value') || 0,
		            disabled: this.get("effective_readonly")
		        });
		        var formatted_value = session.web.format_value(this.get('value') || 0, { type : 'float' });
		        this.$('span').html(formatted_value + '%');
			}
		else
			return this._super();
	}

});

//
session.web.form.One2ManyList=session.web.form.One2ManyList.extend({
    pad_table_to: function (count) {
        if (!this.view.is_action_enabled('create')) {
            this._super(count);
        } else {
            this._super(count > 0 ? count - 1 : 0);
        }

        // magical invocation of wtf does that do
        if (this.view.o2m.get('effective_readonly')) {
            return;
        }

        var self = this;
        var columns = _(this.columns).filter(function (column) {
            return column.invisible !== '1';
        }).length;
        if (this.options.selectable) { columns++; }
        if (this.options.deletable) { columns++; }

        if (!this.view.is_action_enabled('create')) {
            return;
        }

        var $cell = $('<td>', {
            colspan: columns,
            'class': 'oe_form_field_one2many_list_row_add'
        }).append(
            $('<a>', {href: '#'}).text(_t("Add an item"))
                .mousedown(function () {
                    // FIXME: needs to be an official API somehow
                    if (self.view.editor.is_editing()) {
                        self.view.__ignore_blur = true;
                    }
                })
                .click(function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    // FIXME: there should also be an API for that one
                    if (self.view.editor.form.__blur_timeout) {
                        clearTimeout(self.view.editor.form.__blur_timeout);
                        self.view.editor.form.__blur_timeout = false;
                    }
                    self.view.ensure_saved().done(function () {
                        self.view.do_add_record();
                    });
                }));

        var $padding = this.$current.find('tr:first');
        var $newrow = $('<tr class="check_added_to_top">').append($cell);
        $padding=this.view.$el.find('thead:first');

        if ($padding.length===1 && this.$current.find('tr').length>=6) {
        	if (this.view.$el.find('tr.check_added_to_top').length===0)
        		$padding.append($newrow);
        	else
        		return ;
        } else {
        	return ;
        }
    },
});

//Sua gia tri cau o Tag
session.web.form.FieldMany2ManyTags = session.web.form.FieldMany2ManyTags.extend({

	initialize_content: function() {
			var _super=this._super(this);
			var  self = this;
			self.$text = this.$("textarea");

			var bind_x = function () {
			self.$text
				//.textext({ plugins: 'tags' })
				.bind('tagClick', function(e, tag, value, callback)
			        {
			            var pop = new session.web.form.FormOpenPopup(self);
						pop.show_element(
				                self.field.relation,
				                [value['id']],
				                self.build_context(),
				                {
				                    title: _t("Editing VAT"),
				                    target:'new_popup',
				                }
				            );
				            pop.on('write_completed', self, function(){
				            	//if(newValue)
				            	//	callback(newValue, true);
				                //self.display_value = {};
				                self.render_value();
				                self.focus();
				                self.view.do_onchange(self);
				                self.trigger('changed_value'); //Cap nhat onchange khi thay doi value
				            });
			        });

			self.$text.on('keydown', function (e) {
				if (e.which === 69 && e.ctrlKey && e.shiftKey)
					{
					e.preventDefault();
					var pop = new session.web.form.FormOpenPopup(self);
					pop.show_element(
			                self.field.relation,
			                self.get("value"),
			                self.build_context(),
			                {
			                    title: _t("Editing VAT"),
			                    target:'new_popup',
			                }
			            );
			            pop.on('write_completed', self, function(){
			                self.display_value = {};
			                self.render_value();
			                self.focus();
			                self.view.do_onchange(self);
			                self.trigger('changed_value'); //Cap nhat onchange khi thay doi value
			            });
					}
			});
			}
			return $.when(_super,bind_x());
			},
});

//Dat Default cho Base Import
session.web.DataImport = session.web.DataImport.extend({
	init: function (parent, action) {
		var _super=this._super(parent,action);
		var self=this;
		if (typeof(self.res_model)!=='undefined')
			if (self.res_model.search('purchase.order')>=0)
				self.opts[2].value='@';
		return _super;
	}
});


session.web.CrashManager = session.web.CrashManager.extend({
		show_warning: function(error) {
			if (error.type==='Session Expired')
				{
				return window.location.reload();
				};
			return this._super(error);
		},
});


session.web.WebClient.include({
    bind_hashchange: function() {
    	$(document).keydown(function (evt)
    			{
					if (!evt.shiftKey && evt.which===191 && evt.ctrlKey && !evt.altKey)//&& $(':focus').length===0
						{
							if ($('#koe_dialog_help').length===0)
								{
								show_help_dialog();
								}
							else
								{
								$('#koe_dialog_help').dialog('close');
								}
							evt.preventDefault();
						};
    			});
        this._super.apply(this, arguments);
    },
});


session.web.UserMenu =  session.web.UserMenu.extend({
    do_update: function () {
        var self = this;
        var fct = function() {
            var $avatar = self.$el.find('.oe_topbar_avatar');
            $avatar.attr('src', $avatar.data('default-src'));
            if (!self.session.uid)
                return;
            var func = new session.web.Model("res.users").get_func("read");
            return self.alive(func(self.session.uid, ["name", "company_id",'employee_id'])).then(function(res) {
                var topbar_name = res.name;
                if(session.session.debug)
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, session.session.db);
                if(res.company_id[0] > 1)
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, res.company_id[1]);
                self.$el.find('.oe_topbar_name').text(topbar_name);
                if (!session.session.debug) {
                    topbar_name = _.str.sprintf("%s (%s)", topbar_name, session.session.db);
                }
                employee_id=false;
                if (res.employee_id)
                	employee_id=res.employee_id[0]
                var avatar_src = self.session.url('/web/binary/image', {model:'hr.employee', field: 'image_small', id: employee_id});
                $avatar.attr('src', avatar_src);
            });
        };
        this.update_promise = this.update_promise.then(fct, fct);
    },
});

//Dialog Help
var show_help_dialog = function () {
	 var new_dialog=document.createElement('div');
//	 new_dialog.innerHTML='<div id="koe_dialog_help" title="Keyboard Shortcuts" class=""></div>';
	 $(new_dialog)
	 		.load('/kderp_web/static/src/xml/kderp_help.html')
	 		.attr("title","Keyboard Shortcuts")
	 		.attr("class",'koe_dialog_help')
	 		.attr("id",'koe_dialog_help')
	 		.dialog(
			    {
			        autoOpen: false,
			        resizable: false,
			        closeOnEscape: true,
			        close: function () { $(this).remove() },
			        draggable: false,
			        modal: true,
			        width: $(window).width()*90/100.0,
		            height:$(window).height()*90/100.0
			     }).parent()
			     			.addClass('koe_dialog_help')
			     			.find('div.ui-dialog-titlebar').attr("id",'koe_dialog_help_title');


	 $(new_dialog).dialog('open');
	};

//setTimeout template - replace for $(document).ready()
/*
setTimeout(function(){

},500);
 */

//Thanh added

//Cap nhat vi tri cua headers
function UpdateTableHeaders() {
	   $(".oe_list_content").each(function() {

	       var el             = $(this),
	           offset         = el.offset(),
	           scrollTop      = $(window).scrollTop()+121,
	           floatingHeader = $(".floatingHeader", this)
	       if ((scrollTop > offset.top) && (scrollTop < offset.top + el.height())) {
	    	   floatingHeader.css({
	            "visibility": "visible"
	           });
	       } else {
	           floatingHeader.css({
	            "visibility": "hidden"
	           });
	       };
	   });
	}

setTimeout(function(){
	//Test bounce effect
	/*$('.oe_footer').mouseenter(function(){
		$(this).effect('bounce',{times:3},500);
	});*/

	//Hieu ung text cho Chuc mung
	/*var greeting = "___Happy Women's Day!___";
	greeting = "<span class='greeting'>" + greeting + "</span>"
	$(".oe_breadcrumb_item:last-child").append(greeting);
	*/

	//Footer information
//	footerInfo = "Developed by <span style='color:green;font-weight:bold'>KDVN - IT</span>"
//	footerInfo = "<div>" + footerInfo + "</div>"
//	$(".oe_footer").append(footerInfo)

	//Temporary notification - replace the logo position 243x88 | 249x94
//	$(document).ready( function(){
//		$.fn.snow();
//	});
//
	tempNoti = "";
	tempPic =""; //http link of a picture - dropbox?
	if(tempPic!=""){ //Kiem tra bien rong hay khong
		$(".oe_logo img").attr("src",tempPic); //Doi duong dan cua logo
		$(".oe_logo img").css({"width":"243px","height":"88px","margin":"0px"}); //format lai cho dep - margin
	};

},2000);

//var tree_ready = function(current_list){
//	return true;
//	//Freezing table header in tree view
//	//Clone headers
//	if ($(".floatingHeader").length >0){ //Kiem tra floatingHeader co ton tai?
//		$(".floatingHeader").remove()
//		};
//
//	if (current_list.options.search_view){//Kiem tra xem co phai la Tree view o trong form hay khong
//		//su dung first de han che ap dung cho element dau tien, su dung clone(true) de copy event
//		var $floatingHeader = $(".oe_list_header_columns").filter(":first").clone(true);
//		    $floatingHeader.children().width(function (i, val) {
//		    	return $(".oe_list_header_columns").filter(":first").children().eq(i).width();
//		    });
//
//	    	$floatingHeader.css({"width":$(".oe_list_header_columns").filter(":first").width()
//	    		, "height":$(".oe_list_header_columns").filter(":first").height()})
//	    		.addClass("floatingHeader");
//
//	    	//$floatingHeader.css({"width", $(".oe_list_header_columns").filter(":first").width());
//		    //$floatingHeader.css("height",$(".oe_list_header_columns").filter(":first").height()).addClass("floatingHeader");
//		    $(".oe_list_header_columns").filter(":first").before($floatingHeader);
//	};
//  };


	/**
	 * Dieu chinh chieu ngang cua menu topbar cho gon lai de
	 * dung cho notification
	 *
     * Reflow the menu items and dock overflowing items into a "More" menu item.
     * Automatically called when 'menu_loaded' event is triggered and on window resizing.
   */
  session.web.Menu.include({
	    reflow: function() {
	    	var self = this;
	        this.$el.height('auto').show();
	        var $more_container = this.$('.oe_menu_more_container').hide();
	        var $more = this.$('.oe_menu_more');
	        $more.children('li').insertBefore($more_container);
	        var $toplevel_items = this.$el.children('li').not($more_container).hide();
	        $toplevel_items.each(function() {
	            //var remaining_space = self.$el.parent().width() - $more_container.outerWidth();
	        	var remaining_space = self.$el.parent().width()*0.8 - $more_container.outerWidth();
	            self.$el.parent().children(':visible').each(function() {
	                remaining_space -= $(this).outerWidth();
	            });
	            if ($(this).width() > remaining_space) {
	                return false;
	            }
	            $(this).show();
	        });
	        $more.append($toplevel_items.filter(':hidden').show());
	        $more_container.toggle(!!$more.children().length);
	        // Hide toplevel item if there is only one
	        var $toplevel = this.$el.children("li:visible");
	        if ($toplevel.length === 1) {
	            $toplevel.hide();
	        }
	    },
  });


  session.web.UserMenu = session.web.UserMenu.extend({
	  /**
	   * Ke thua on_menu_about de khi
	   * click vao About thi chuyen luon sang Developer Mode
	   */
	    on_menu_about: function() {
	    	if (window.location.href.search("debug")==-1){
            	window.location = $.param.querystring( window.location.href, 'debug');
	    	} else {
	    		window.location = window.location.href.replace("debug","");
	    	};
	    },

	    /**
	     * Huong dan su dung cua KDVN
	     */
	    on_menu_help: function() {
	        window.open('https://docs.google.com/document/d/1nLNlWfbR8gCEodgGw9xjeYElTvnmoT_gac5ADejRn0s/pub', '_blank');
	    },

	    on_menu_password: function() {
	        var self = this;
	        if (!this.getParent().has_uncommitted_changes()) {
	            self.rpc("/web/action/load", { action_id: "kderp_web.action_change_password" }).done(function(result) {
	                result.res_id = session.session.uid;
	                self.getParent().action_manager.do_action(result);
	            });
	        }
	    },
  });

  /**
   * Tao su kien hover cho koe_many2one_image
   */
  /*session.web.form.FieldMany2OneImage = session.web.form.FieldMany2OneImage.extend({
	  events: {
		"mouseenter .koe_many2one_image": "img_enter",
		"mouseleave .koe_many2one_image": "img_leave"
	  },
	  img_enter: function(){
		  this.$el.find(".koe_many2one_image").css({width: '+=24px',height: 'auto'});
	  },
	  img_leave: function(){
		  this.$el.find(".koe_many2one_image").css({width: '',height:''});
	  }
  });*/



  /**
   * Sua lai ham configure_pager trong ListView
   * Thay the chuoi 1-80 of xxxx bang chuoi 1-80|xxxx cho gon
   *
   * Su dung cu phap $.extend(this.PROPERTY, {NEW VALUE})o trong init
   * de them cac value moi vao
   *
   * load_list ke thua de sua loi hien thi so trang
   */
  session.web.ListView.include({

	  init: function(parent, dataset, view_id, options) {
	    var self = this;
	    this._super(parent, dataset, view_id, options);
	    $.extend(this.events,{'mouseenter thead tr.oe_list_header_columns':'header_hover'});
	    //_.extend(source, destination) dung de them doi tuong vao trong doi tuong
	  },

	  configure_pager: function(dataset){
		this._super(dataset);
		var spager_replace = this.$pager.find('.oe_list_pager_state').text().replace(" of ","|");
		this.$pager.find('.oe_list_pager_state').text(spager_replace);
	  },

	  header_hover: function(){
		  //console.log("hovering over my head...");
	  },

	  load_list: function(data){
		  var self = this;
		  this._super(data);
		  $(".oe_list_header_columns").addClass("TEST");
//		  console.log(this.$el.find(".oe_list_header_columns");
	  },

	  view_loading: function(r){
		  var self = this;
		  this._super(r);
	  },

  });

  /**
   * Ke thua class WebClient
   *
   * show_login: bo sung kiem tra kich thuoc man hinh
   * co the la 1 loat cac kiem tra khac truoc khi cho chay ung dung:
   * TODO: browser; windows
   *
   * show_application: kiem tra chieu ngang man hinh
   *
   * kderp_drawlayout: de tinh toan gia tri min-width cua oe_lefbar
   * CSS khong hoan hao trong truong hop nay do co 1 so element su dung fixed position
   *
   * kderp_refresh: su dung khi co gian man hinh
   * TODO: can refresh ca floating_header
   *
   */
  session.web.WebClient.include({
	  start: function(){
	  	var self = this;
	  	this._super();
	  	$(window).resize(function(){
	  		self.kderp_drawlayout(self);
	  	});
	  },
	  show_login: function(){
		if (screen.width >= 1024){ //1920?
	        this.toggle_bars(false);

	        var state = $.bbq.getState(true);
	        var action = {
	            type: 'ir.actions.client',
	            tag: 'login',
	            _push_me: false,
	        };

	        this.action_manager.do_action(action);
	        this.action_manager.inner_widget.on('login_successful', this, function() {
	            this.show_application();        // will load the state we just pushed
	        });
		} else {
			alert("The monitor is too small - Please adjust to at least 1024 width! - THANK YOU");
			return;
		};
    },

    show_application: function(){
    	var self = this;
    	this._super();
    	this.kderp_drawlayout(self);

    },

    kderp_drawlayout: function(container){
    	var window_width = $(window).width();
    	var leftbar_ratio = 18;
    	var leftbar_min_width = (window_width*leftbar_ratio)/100;
    	container.$el.find(".openerp .oe_leftbar").css({"min-width":leftbar_min_width});
    	container.$el.find(".openerp .oe_logo").width($(".openerp .oe_leftbar").width());
    	$(".openerp .oe_leftbar .koe_leftbar").width($(".openerp .oe_leftbar").width());
    	$(".openerp .oe_leftbar .koe_leftbar").height($(window).height()-($(".oe_topbar").height()+$(".oe_logo").height()+$(".oe_footer").height()));
    },

  });

  /**
   * Customize Search View
   * Khi click vao mot dieu kien search co the sua duoc de search tiep
   * Luu y: su dung ham trim() de remove cac ky tu thua de gay loi khi search
   * TODO: sua truc tiep tai search value va cap nhat lai search
   * Ke thua start de them thuoc tinh draggable va event dragstart de bat co dang bat dau keo tha
   * va se khong thuc hien su kien click khi keo tha
   */
  session.web.search.FacetView.include({
  	init: function(parent, model){
  		var self = this;
  		this._super(parent, model);
		//TODO Later revise it
		//this.$el.parent().draggable();
		//self.isDragging = false;

  		$.extend(this.events,{
			//'dragstart':function(e){
             //   //Set flag for when click disable when click
			//	self.isDragging = true;
			//},
  			'click': function(e){
                //if (self.isDragging) {
                //    self.isDragging = false;
                //    e.preventDefault();
                //}
                //When click close facet remove
				if ($(e.target).is('.oe_facet_remove')) {
                            this.model.destroy();
                            this.$el.focus();
                            return false;
                        }
                //When click to facet value
                else if ($.inArray('oe_facet_value', e.target.classList) >= 0) {
                        var search_value = e.target.textContent.trim();
                        //When facevalue > more than 1 item
                        if (this.$el.find('.oe_facet_value').length > 1) {
                            e.target.remove();
                            //remove a clicked facet value
                            this.model.values.models = this.model.values.models.filter(function (item) {
                                return item.get('value') != search_value;
                            });
                            //Refresh search
                            this.__parentedParent.do_search();
                        }
                        else
                            this.model.destroy();
                        $('.oe_searchview_input:last-child').focus().text(search_value);
                    }
  			},
  		});
  	},

  });

  /**
   * Cho phep dinh nghia so luong ban ghi su dung o dropdown list trong
   * truong many2one: options="{'limit':8}"
   * TODO: bo sung them cac options khac
   */
  session.web.form.CompletionFieldMixin = _.extend(session.web.form.CompletionFieldMixin,{
  	init: function(){
  		if (typeof this.options.limit ==='number'){
  			this.limit = this.options.limit;
  		} else {
  			this.limit = 7;
  			}
        this.orderer = new session.web.DropMisordered();
  	}
  })


   /**
   * Trinh bay phan custom search list de chi show ra khi click vao Custom Filters
   * Khi co qua nhieu custom search list se lam roi search drawer
   * toggleClass(class,false/true) tuong duong tat/bat
   */
  session.web.search.CustomFilters = session.web.search.CustomFilters.extend({
  	start: function(){
  		var self = this;
		this._super();
		$('.openerp .oe_searchview_custom_list').hide();
		$('.openerp .oe_searchview_custom_saved_list h3').on('click',function(){
			if ($('.openerp .oe_searchview_custom_list li').length > 0) {
				$('.openerp .oe_searchview_custom_list').toggle();
			}
		});
  	},

  	show_custom_filters: function(){
  		$('.openerp .oe_searchview_custom_list').toggle();
  	},

  	append_filter: function(filter){
  		var self = this;
  		this._super(filter);
		$('.openerp .oe_searchview_custom_list li').on('click',function(){
			$('.oe_searchview').toggleClass('oe_searchview_open_drawer',false);
		});
  	},

  })

	/**
	 * Bo sung dieu kien like phuc vu cho
	 * trinh bay xml: attrs=
	 * Ke thua ham, sua dieu kien cua arguments,
	 * arguments: la dang mang [array1, object]: array1 la domain, object la danh sach cac truong va gia tri
	 * Tim dieu kien trong domain, neu co tu indexOf thi se kiem tra dieu kien theo ham Index
	 * Kq la True: tra ve dieu kien code!=false (dieu kien luon dung),
	 * Kq la False: tra ve dieu kien code=false (dieu kien luon sai),
	 * TODO: ke thua ham chua lam
	 */
  	var old_compute_domain = session.web.form.compute_domain; //Link compute_domain
  	session.web.form.compute_domain = function() {
	var tmp=$.extend(true,[],arguments);//Clone Object Arguments
	if (tmp[0][0])
		{
		var vdomain=tmp[0][0];
		if (typeof vdomain=='object')//Kiem tra domain phai la dang array khong phai la cac ky tu dac biet nhu '|', &, !
			if (vdomain[1].toLowerCase()==='indexof')
				{
					var field = tmp[1][vdomain[0]];
					var value = vdomain[2];
			        if (!field) {
			            throw new Error(_.str.sprintf(
			                _t("Unknown field %s in domain %s"),
			                value, JSON.stringify(value)));
			        }
			        var field_value = field.get_value ? field.get_value() : field.value;
			        tmp[0][0][2]='false'
			        if (!field_value)
			        	tmp[0][0][1]='='
			        else
    				        if (field_value.toLowerCase().indexOf(value.toLowerCase())>=0)
    				        	tmp[0][0][1]='!='
    				        else
    				        	tmp[0][0][1]='='
				}
		};
		var result = old_compute_domain.apply(this, tmp);
		return result;
  	};
};