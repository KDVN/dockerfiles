# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
import time
class wizard_kderp_open_stock_proudcts(osv.osv_memory):
    """This model is Wizard model, using for select """
    _name = "kderp.open.stock.products"

    _columns = {
        'stock_ids':fields.many2many('stock.location',"kderp_open_stock_open_products",'open_product_id','location_id',string="Stocks",help='Please select Job Stock or General Stock, not allow select Job and General Stock one time'),
        'from_date':fields.date('From Date'),
        'to_date':fields.date('To Date'),
        'compute_child':fields.boolean("Related Stocks?"),
        'all_product':fields.boolean("All Products",help='Checked will list all product otherwise only list Product using in Stock and Period'),
        # build the list of ids of children of the location given by id
    }
    _defaults ={
        'from_date':'2015-10-14'
    }
    def open_products(self, cr, uid, ids, context):
        #TODO later add domain (only product using for stock) 'domain': "[('id')]"

        if not context:
            context = {}
        open_form_data = self.browse(cr, uid, ids[0],context)

        location_ids = []
        check_stock_type = {}
        stock_string = ""
        for stock in open_form_data.stock_ids:
            location_ids.append(stock.id)
            stock_string = stock.name if not stock.code else (stock.code + "-" + stock.name)
            check_stock_type[stock.general_stock] = True
            if len(check_stock_type.keys())>1:
                raise osv.except_osv("KDERP Warning", "Can't select general stock with job stock !, you can select general stock or Job Stock")
        if not location_ids:
            location_ids = self.pool.get('stock.location').search(cr, uid, [('general_stock','=',True)])
            if not location_ids:
                return False
        stock = location_ids and self.pool.get('stock.location').browse(cr, uid, location_ids[0])
        stock_string = stock.name if not stock.code else (stock.code + "-" + stock.name)

        stock_string = ("%d Stocks" % len(location_ids)) if len(location_ids)>1 else stock_string

        context['tree_view_ref'] = 'kderp_stock_inout.view_kderp_product_for_stock_tree'
        context['from_date'] = open_form_data.from_date
        context['to_date'] = open_form_data.to_date
        context['location'] = location_ids and location_ids[0]
        context['location_ids'] = location_ids
        context['compute_child'] = open_form_data.compute_child

        pp_obj = self.pool.get('product.product')
        domain = [('type','!=','service')]
        if not open_form_data.all_product:
            product_ids = pp_obj.find_product_in_period(cr, uid, location_ids, context)
            domain += [('id','in',product_ids)]

        return {
                    'type': 'ir.actions.act_window',
                    'name': "Products @ %s" % stock_string,
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'context': context,
                    'res_model': 'product.product',
                    'domain': domain,
                    'auto_refresh': 1
                    }