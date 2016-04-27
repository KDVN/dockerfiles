
import re
import time

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_round, float_is_zero, float_compare
from openerp.tools.translate import _

class res_currency(osv.osv):
    _name = "res.currency"
    _description = "Currency"
    _inherit = "res.currency"
    
    _sql_constraints=[('kderp_currency_unique','unique(name)','Currency must be unique !')]
    
    def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount,
                round=True, currency_rate_type_from=False, currency_rate_type_to=False, context=None):
        if not context:
            context={}
        
        #Change the way compute (Input Exrate follow Vietnam)
        tmp=from_currency_id
        from_currency_id = to_currency_id
        to_currency_id = tmp
        
        if not context:
            context = {}
        if not from_currency_id:
            from_currency_id = to_currency_id
        if not to_currency_id:
            to_currency_id = from_currency_id
            
        xc = self.browse(cr, uid, [from_currency_id,to_currency_id], context=context)
        from_currency = (xc[0].id == from_currency_id and xc[0]) or xc[1]
        to_currency = (xc[0].id == to_currency_id and xc[0]) or xc[1]
        
        if (to_currency_id == from_currency_id) and (currency_rate_type_from == currency_rate_type_to):
            if round:
                return self.round(cr, uid, from_currency, from_amount)
            else:
                return from_amount
        else:
            if context.get('invoice_id',False):
                #Kiem tra xem tra tien hay khong de cap nhat lai ti gi
                user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
                ai_obj=self.pool.get('account.invoice')
                ai=ai_obj.browse(cr, uid, context['invoice_id'])
                kr_exrate=0
                chk_writeoff=False
                
                for kr in ai.received_ids:
                    chk_writeoff=kr.writeoff
                    if kr.currency_id.id==user.company_id.currency_id.id:
                        kr_exrate=kr.amount/ai.amount_total if ai.amount_total else 0
                    else:
                        kr_exrate=kr.exrate
                        
                if kr_exrate and not chk_writeoff:
                    to_exrate = kr_exrate
                else:
                    to_exrate = self.pool.get('account.invoice').read(cr,uid,context['invoice_id'],['exrate'])['exrate']
                    
                if to_currency_id==user.company_id.currency_id.id: #If convert from Company Currency to Other
                    from_exrate = user.company_id.currency_id.rate
                    exrate = from_exrate/to_exrate
                else:
                    exrate = to_exrate
                
                if round:
                    return self.round(cr, uid, from_currency, from_amount*exrate)
                else:
                    return from_amount*exrate            
            
            context.update({'currency_rate_type_from': currency_rate_type_from, 'currency_rate_type_to': currency_rate_type_to})
            rate = self._get_conversion_rate(cr, uid, from_currency, to_currency, context=context)
            if round:
                return self.round(cr, uid, from_currency, from_amount * rate)
            else:
                return from_amount * rate
            
    _columns={
              'pattern':fields.char("Pattern",size=32)
              }
    _defaults={
               'pattern':lambda *a:"#,##0.00"
               }
res_currency()