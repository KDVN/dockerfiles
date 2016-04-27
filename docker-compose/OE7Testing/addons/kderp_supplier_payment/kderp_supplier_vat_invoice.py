from osv import osv, fields
from osv.orm import intersect
import time
import openerp.addons.decimal_precision as dp
import openerp.exceptions

#Red Invoice
class kderp_supplier_vat_invoice(osv.osv):
    _name="kderp.supplier.vat.invoice"
    _description="KDERP Supplier VAT Invoice Information"
    
    def unlin1k(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        unlink_ids = []
        for ksvi in self.browse(cr, uid, ids):
            if ksvi.kderp_supplier_payment_ids or ksvi.kderp_supplier_payment_expense_ids:
                raise openerp.exceptions.Warning('You cannot delete an VAT Invoice which is attached to Supplier Payment.')
            else:
                unlink_ids.append(ksvi.id)
        return osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
    
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
        return this_time
    
    def _new_date(self, cr, uid, context={}):
        this_time=time.strftime('%Y-%m-%d')
        if context:
            if 'received_date' in context:
                this_time=context['received_date']
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
        return this_time
    
    def _new_total(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            po_amt=self.pool.get("purchase.order").read(cr,uid,exp_id,['amount_total'])['amount_total']            
            this_time=po_amt
            
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            po_amt=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['amount_total'])['amount_total']            
            this_time=po_amt
        return this_time
    
    def _new_total_vnd(self, cr, uid, context={}):
        if not context:
            context={}
        this_time=0
        if context.get('order_id',False):
            exp_id = context.get('order_id',0)
            po_amt=self.pool.get("purchase.order").read(cr,uid,exp_id,['amount_total','exrate'])
            this_time = po_amt['amount_total'] * po_amt['exrate']
            
        if context.get('expense_id',False):
            exp_id = context.get('expense_id',0)
            po_amt=self.pool.get("kderp.other.expense").read(cr,uid,exp_id,['amount_total'])['amount_total']            
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
        return this_time
    
#     def _get_state(self, cr, uid, ids, field_name, arg, context=None):
#         res = {}
#         cur_obj=self.pool.get('res.currency')
#         val = 0.0 
#         for ksvi in self.browse(cr, uid, ids, context=context):
#             done=True
#             for payment in ksvi.kderp_supplier_payment_ids:
#                 if payment.state<>'paid': done=False
#                 
#             for payment in ksvi.kderp_supplier_payment_expense_ids:
#                 if payment.state<>'paid': done=False
#             res[ksvi.id]='done' if done else 'draft'
#         return 'draft'
    
    def _get_invoice_from_supplier_payment_expense(self, cr, uid, ids, context=None):
        result = {}
        kspe_obj = self.pool.get('kderp.supplier.payment.expense')
        for kspe in kspe_obj.browse(cr, uid, ids):
            for vat in kspe.kderp_vat_invoice_ids:
                result[vat.id]=True
        return result.keys()

    def _get_invoice_from_supplier_payment(self, cr, uid, ids, context=None):
        result = {}
        kspe_obj = self.pool.get('kderp.supplier.payment')
        for kspe in kspe_obj.browse(cr, uid, ids):
            for vat in kspe.kderp_vat_invoice_ids:
                result[vat.id]=True
        return result.keys()
    
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
        return this_time
    
    _columns={
             'name':fields.char('Invoice No.',size=32,required=True),
             'currency_id':fields.many2one('res.currency','Curr.',required=True),
             
             'date':fields.date('Date',),              
             'received_date':fields.date('Received Date',),
             'to_accounting_date':fields.date('To Accounting Date',),
             'returned_date':fields.date('Returned Date',),
             
             'subtotal':fields.float('Sub-Total',digits_compute= dp.get_precision('Amount'),),
             #'taxes_id': fields.many2many('account.tax', 'supplier_vat_tax', 'supplier_vat_id', 'tax_id', 'Taxes',),
             'tax_per':fields.float('VAT (%)',digits_compute= dp.get_precision('Amount')),
             'amount_tax':fields.float('VAT',digits_compute= dp.get_precision('Amount')),
             'total_amount':fields.float('Total',digits_compute= dp.get_precision('Amount'),),
             'rate':fields.float('@',),
             'equivalent_vnd':fields.float('In VND',digits_compute= dp.get_precision('Bduget'),),
             'notes':fields.text('Notes'),
             
             'kderp_supplier_payment_ids':fields.many2many('kderp.supplier.payment','kderp_supplier_payment_vat_invoice_rel', 'vat_invoice_id','payment_id','VAT Invoices',),
             'kderp_supplier_payment_expense_ids':fields.many2many('kderp.supplier.payment.expense','kderp_supplier_payment_expense_vat_invoice_rel', 'vat_invoice_id','payment_expense_id','VAT Invoices',),
             'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
#             'state':fields.function(_get_state,type='selection',method=True,selection=[('draft','Draft'),('done','Done')],string='State')
#              ,                                     store={
#                                              'kderp.supplier.payment.expense': (_get_invoice_from_supplier_payment_expense, ['state'], 30),
#                                              'kderp.supplier.payment': (_get_invoice_from_supplier_payment, ['state'], 30),
#                                              'kderp.supplier.vat.invoice': (lambda self, cr, uid, ids, c={}: ids, ['subtotal','taxes_id'], 15),
#                                             }),
             }
    _defaults={
               'currency_id':_get_currency,
               'state':lambda *x:'draft',
               'tax_per':new_per,
               'subtotal':_new_subtotal,
               'amount_tax':_new_vat,
               'total_amount':_new_total,
               'equivalent_vnd':_new_total_vnd,
               'rate':_new_exrate,
               'received_date':_new_date,
               }
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            ids = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
            
            if not ids:
                check=name.replace(',','')
                if check.isdigit():
                    ids = self.search(cr, user, [('total_amount','=',check)]+ args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    def onchange_totalamount(self, cr, uid, ids, amount, qvnd, rate,type):
        if type=='ev':
            value={'rate':round(qvnd/amount,2) if amount<>0 else 0}
        else:
            value={'equivalent_vnd':round(amount*rate,2)}

        return {'value':value}
    
    def on_changevalue_per(self, cr, uid, ids, amount, tax_per, amount_tax=0,dump = 0):
        if abs(amount*tax_per/100.0-amount_tax)<=2:
            amount_tax=amount_tax
        else:
            amount_tax=amount*tax_per/100.0
        result={'amount_tax':amount_tax,'total_amount':amount_tax+amount}
        return {'value':result}
    
    def on_changevalue(self, cr, uid, ids, amount, amount_tax,dump = 0):
        result={'total_amount':amount_tax+amount}
        return {'value':result}
    
kderp_supplier_vat_invoice()
