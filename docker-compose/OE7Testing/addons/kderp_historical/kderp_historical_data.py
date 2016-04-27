import operator
import time

from osv import osv, fields
from osv.orm import intersect

import tools.sql

from tools import config
from tools.translate import _

import openerp.addons.decimal_precision as dp

class purchase_order_line(osv.osv):
    _name = "purchase.order.line"
    _inherit= "purchase.order.line"
    
    _description = "KDERP Historical Data"
    
    _order = "sequence,product_id,partner_id"
    
    def _get_price_final(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        cur_obj=self.pool.get('res.currency') 
        for pol in self.browse(cr, uid, ids, context=context):
            res[pol.id] = (pol.final_subtotal/pol.product_qty) if pol.product_qty else 0
            res[pol.id] = cur_obj.round(cr, uid, pol.order_id.pricelist_id.currency_id, res[pol.id])
        return res
    
    def _get_rate_to_usd(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        usd_ids = cur_obj.search(cr, uid,[('name','=','USD')])
        if usd_ids:
            usd_id=usd_ids[0]
        else:
             usd_id=False
        if usd_id:
            for pol in self.browse(cr, uid, ids, context=context):
                res[pol.id] = cur_obj.compute(cr, uid, pol.order_id.pricelist_id.currency_id.id, usd_id, 1,round=False,context={'date': pol.order_id.date_order})
        return res    
    
    def _get_line_from_order(self, cr, uid, ids, context=None):
        result = {}
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for line in po.order_line: 
                result[line.id] = True
        return result.keys()
    
    _columns={
                'currency_id': fields.related('order_id', 'currency_id', type="many2one", relation="res.currency", string="Currency",readonly=True, required=True),
                'po_state': fields.related('order_id', 'state', type="char", string="PO State",size=32,readonly=True),
                
                'partner_id':fields.related('order_id','partner_id',relation='res.partner',type='many2one',string='Link to Partner',store=True,select=1),
                
                'after_negotiation':fields.function(_get_price_final,string='After Negotiation',digits_compute=dp.get_precision('Amount'),type='float',
                                                 method=True,
                                                 store={
                                                        'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','plan_qty'], 20),
                                                        'purchase.order': (_get_line_from_order, ['discount_amount','special_case','state'], 20),
                                                        }),
                'exchange_rate_usd_to_other':fields.function(_get_rate_to_usd,type='float',method=True,string='Exchange to USD',digits_compute=dp.get_precision('Percent'))
                }
purchase_order_line()


class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    _columns = {
                'kderp_price_history_ids': fields.one2many("purchase.order.line",'product_id',"History",readonly=1),        
                }
product_product()

class res_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    
    _columns = {
                'kderp_price_history_ids': fields.one2many("purchase.order.line",'partner_id',"Price History",readonly=1),        
                }
res_partner()