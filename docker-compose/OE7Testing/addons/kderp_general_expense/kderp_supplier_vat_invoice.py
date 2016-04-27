from osv import osv, fields
from osv.orm import intersect
import time
import openerp.addons.decimal_precision as dp
import openerp.exceptions

#Red Invoice
class kderp_supplier_vat_invoice(osv.osv):
    _name="kderp.supplier.vat.invoice"
    _inherit="kderp.supplier.vat.invoice"  
    _description="KDERP Supplier VAT Invoice Information"
    
    def _new_subtotal(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            po_amt=self.pool.get("purchase.order").read(cr,uid,exp_id,['final_price'])['final_price']            
            this_time=po_amt
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            po_amt=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['amount_untaxed'])['amount_untaxed']            
            this_time=po_amt
        if context.get('general_expense_id',False):
            ge_id = context.get('general_expense_id',0)
            po_amt=self.pool.get("kderp.general.expense").read(cr,uid,ge_id,['sub_total'])['sub_total']            
            this_time=po_amt
        return this_time
    
    def _new_vat(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            amount_tax=self.pool.get("purchase.order").read(cr,uid,exp_id,['amount_tax'])['amount_tax']            
            this_time=amount_tax
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            po_amt=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['amount_tax'])['amount_tax']            
            this_time=po_amt
        if context.get('general_expense_id',False):
            ge_id=context.get('general_expense_id',0)
            ge_amt=self.pool.get("kderp.general.expense").read(cr,uid,ge_id,['amount_tax'])['amount_tax']
            this_time=ge_amt
        return this_time
    
    def new_per(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            po=self.pool.get("purchase.order").read(cr,uid,exp_id,['amount_tax','final_price'])
            amt=po['final_price']
            tax=po['amount_tax']            
            this_time=(tax/amt) if amt else 0
            this_time=this_time*100.0
            
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            exp=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['amount_tax','amount_untaxed'])
            amt=exp['amount_untaxed']
            tax=exp['amount_tax']            
            this_time=(tax/amt) if amt else 0
            this_time=this_time*100.0
                
        if context.get('general_expense_id',False):
            exp_id = context.get('general_expense_id',0)
            exp=self.pool.get("kderp.general.expense").read(cr,uid,exp_id,['amount_tax','sub_total'])
            amt=exp['sub_total']
            tax=exp['amount_tax']            
            this_time=(tax/amt) if amt else 0
            this_time=this_time*100.0
        return this_time
    
    def _new_exrate(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            po_amt=self.pool.get("purchase.order").read(cr,uid,exp_id,['exrate'])['exrate']
            this_time=po_amt
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            po_amt=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['exrate'])['exrate']
            this_time=po_amt
        if context.get('general_expense_id',False):
            exp_id = context.get('general_expense_id',0)
            po_amt=self.pool.get("kderp.general.expense").read(cr,uid,exp_id,['exrate'])['exrate']
            this_time=po_amt
        return this_time
    def _get_currency(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            curr_id=self.pool.get("purchase.order").read(cr,uid,exp_id,['currency_id'])['currency_id'][0]
            this_time=curr_id
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            curr_id=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['currency_id'])['currency_id'][0]
            this_time=curr_id
        if context.get('general_expense_id',False):
            exp_id = context.get('general_expense_id',0)
            curr_id=self.pool.get("kderp.general.expense").read(cr,uid,exp_id,['currency_id'])['currency_id'][0]
            this_time=curr_id
        return this_time
   
    _columns={
           
            
             }
    _defaults={
               'currency_id':_get_currency,
               'subtotal':_new_subtotal,
               'amount_tax':_new_vat,
               'tax_per':new_per,
               'rate':_new_exrate,
               }
    
   
    
kderp_supplier_vat_invoice()
