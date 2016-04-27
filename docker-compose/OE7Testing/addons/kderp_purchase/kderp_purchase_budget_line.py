import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_purchase_budget_line(osv.osv):
    _name='kderp.purchase.budget.line'
    _description='Purchase Budget Line'
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = []
        for kpbl in self.browse(cr,uid,ids):
            name = kpbl.purchase_order_id.name
            res.append((kpbl.id, name))
        return res
    
    def _get_exrate(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pbl in self.browse(cr,uid,ids):
            res[po.id] = pbl.purchase_order_id.exrate
        return res
    
    def _get_purchase_order_line(self, cr, uid, ids, context=None):
        result = []
        for pol in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result.append(pol.purchase_budget_line.id)
        return result

    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = []
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for line in po.purchase_budget_line:
                result.append(line.id)
        return result
    
    _columns={              
              'purchase_order_id':fields.many2one('purchase.order','Purchase line',ondelete="restrict",required=True),
              
              'amount_currency': fields.float('Amount Currency',  digits_compute=dp.get_precision('Account')),
              'amount':fields.float('Amount',digits_compute=dp.get_precision('Budget')),
              'tax_amount': fields.float('Tax Amount', digits_compute=dp.get_precision('Account'), select=True),
              
              #File Function Store
              'budget_id':fields.many2one('account.budget.post',"Budget"),
              'account_analytic_id':fields.many2one('account.analytic.account','Job',required=True),

              #Related Field
              'exrate':fields.function(_get_exrate, string='Exrate', type='float', required=True, select=True,digits_compute=dp.get_precision('Account'),
                                store = {
                                    'purchase.order': (_get_purchase_order, ['currency_id','pricelist_id','date_order'], 20)
                                }),
                            
              'currency_id':fields.related('purchase_order_id', 'currency_id', string='Curr.', type='many2one', relation='res.currency', required=True, select=True,
                                store = {
                                    'purchase.order': (_get_purchase_order, ['period_id'], 20)
                                }),
              'period_id':fields.related('purchase_order_id', 'period_id', string='Period', type='many2one', relation='account.period', required=True, select=True,
                                store = {
                                    'purchase.order': (_get_purchase_order, ['period_id'], 20)
                                }),
              'date': fields.related('purchase_order_id','date_order', string='Date of Order', type='date', required=True, select=True,
                                store = {
                                    'purchase.order': (_get_purchase_order, ['date_order'], 20)
                                }),
              }
kderp_purchase_budget_line()


class purchase_order_line(osv.osv):
    _name='purchase.order.line'
    _inherit='purchase.order.line'
    _description='Customize Purchase Order line for Kinden'
    _columns={
              'purchase_budget_line':fields.many2one('kderp.purchase.budget.line','Purchase Order Budget Line',ondelete="set null")
              }
purchase_order_line()