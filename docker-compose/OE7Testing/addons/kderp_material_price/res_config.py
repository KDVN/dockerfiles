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
class kderp_price_history_config_settings(osv.osv_memory):
    _name = 'kderp.price.history.config.settings'
    _inherit = 'res.config.settings'    
    
    _columns = {
                'price_history_after_days_ood':fields.integer('Day(s)', required=True, 
                                                               help="""Number of the day from Updated Price to Current greater than one will be warning"""), 
                'price_different': fields.float('Different (%)', required=True, 
                                                help='Number in percent, this number is different rate from Unit Price and latest Price in OE'), 
                'baseon_typeprice':fields.selection(TYPE_PRICE, 'Base on', required=True)
    }
    
    #Write value to res company when click save in config    
    def set_price_history_after_days_ood(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({'price_history_after_days_ood': config.price_history_after_days_ood})
        
    def set_price_different(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({'price_different':config.price_different})
        
    def set_baseon_typeprice(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({'baseon_typeprice': config.baseon_typeprice})
    _defaults = {
                'price_history_after_days_ood': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.price_history_after_days_ood, 
                'price_different': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.price_different, 
                'baseon_typeprice': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.baseon_typeprice
        }
        
class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    
    _columns = {
                'price_history_after_days_ood': fields.integer('Day(s)', required=True, 
                                                               help="""Number of the day from Updated Price to Current greater than one will be warning"""), 
                'price_different': fields.float('Different', required=True, 
                                                help='Number in percent, this number is different rate from Unit Price and latest Price in OE'), 
                'baseon_typeprice':fields.selection(TYPE_PRICE, 'Base on', required=True)
                }