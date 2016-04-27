# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv as models

class StockLocation(models.Model):
    """
        Inherit stock location, customize for Kinden Vietnam
    """
    _inherit = 'stock.location'
    _name = 'stock.location'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        stock_usage = context.get('stock_usage', False)
        if stock_usage:
            if stock_usage.find('!!')>=0:
                compareSign = '!='
                compareValue = stock_usage[2:]
            else:
                compareSign = '='
                compareValue = stock_usage
            args += [('usage',compareSign, compareValue)]
        return super(StockLocation, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)

    def _get_products_list(self, cr, uid, ids, name, args, context = {}):
        """ Return product using for stock in current period
        """
        res = {}
        pp_obj = self.pool.get('product.product')
        ctx = context.copy()
        ctx = ctx or {}
        ctx['compute_child'] = True
        for location_id in ids:
            pr_ids = pp_obj.find_product_in_period(cr, uid, location_id, ctx)
            res[location_id] = pr_ids
        return res

    # Fields declaration
    _columns = {
                'product_ids':fields.function(_get_products_list,type='one2many',relation='product.product',string="Products")
                }