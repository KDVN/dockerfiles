# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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

TYPE_PRICE = (('ref_avg', 'Average Price'),
                  ('ref_min', 'Min Price'),
                  ('ref_max', 'Max Price'),
                  ('ref_latest','Latest Price')
                  )
class kderp_get_price_from_history_stock(osv.osv_memory):
    _name = 'kderp.get.price.from.history.stock'
    _inherit = 'res.config.settings'

    _columns = {
                'stock_price_different': fields.float('Different (%)', required=True,
                                                help='Number in percent, this number is different rate from Unit Price and latest Price in OE'),
                'stock_baseon_typeprice':fields.selection(TYPE_PRICE, 'Base on', required=True)
    }

    #Write value to res company when click save in config
    def set_price_different(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({'stock_price_different':config.stock_price_different})

    def set_baseon_typeprice(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({'stock_baseon_typeprice': config.stock_baseon_typeprice})

    _defaults = {
                'stock_price_different': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.stock_price_different,
                'stock_baseon_typeprice': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.stock_baseon_typeprice
        }

class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    
    _columns = {
                'stock_price_different': fields.float('Different', required=True,
                                                help='Number in percent, this number is different rate from Unit Price and latest Price in OE'), 
                'stock_baseon_typeprice':fields.selection(TYPE_PRICE, 'Base on', required=True)
                }