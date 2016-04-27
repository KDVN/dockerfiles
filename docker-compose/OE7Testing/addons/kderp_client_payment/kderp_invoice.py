#import operator
#import time
from osv import osv, fields
from osv.orm import intersect
#import tools.sql
#from tools import config
#from tools.translate import _
#from mx import DateTime

#KDERP Invoice
class kderp_invoice(osv.osv):
    _name="kderp.invoice"
    _description="KDERP Invoice Information"
        
    _columns={
             'name':fields.char('Invoice No.',size=16,required=True),
             'date':fields.date('Date',required=True),
             'type':fields.selection([('in_invoice','Supplier'),('out_invoice','Customer')],'Type',select=True),
             'customer':fields.many2one('res.partner','Customer'),
             'currency_id':fields.many2one('res.currency','Currency'),
             'subtotal':fields.float('Sub-Total'),
             'tax_percent':fields.float('VAT (%)'),
             'amount_tax':fields.float('Tax'),
             'total_amount':fields.float('Total'),
             'notes':fields.text('Notes')            
             }
    _defaults={
               'type':lambda *x: 'out_invoice',
               'subtotal':lambda *x:0.0,
               'tax_percent':lambda *x:0.0,
               'amount_tax':lambda  *x:0.0,
               'total_amount':lambda *x:0.0
               }
    
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        res = []
        reads = self.read(cr, uid, ids, ['name','date'], context)
        for record in reads:
            name=''
            if record and record['date']:
                name = record['name']+" - "+record['date']
            else:
                name = record['name']
            res.append((record['id'], name))        
        return res
    
    def on_changevalue(self,cr,uid,ids,amount,tax_percent,amount_tax=False):
        if amount_tax==False:
            amount_tax=amount*tax_percent/100.0
            total_amount=amount+amount_tax
            result={'value':{'amount_tax':amount_tax,'total_amount':total_amount}}
        else:
            total_amount=amount+amount_tax
            result={'value':{'amount_tax':amount_tax,'total_amount':total_amount}}
        return result
    
kderp_invoice()

class kderp_payment_vat_invoice(osv.osv):
    _name = 'kderp.payment.vat.invoice'
    _description = 'KDERP Payment VAT Invoice'
    _rec_name = 'vat_invoice_id'
    
    _columns={
              'payment_id':fields.many2one('account.invoice','Client Payment',required=True),
              'vat_invoice_id':fields.many2one('kderp.invoice','VAT No.',required=True, ondelete='restrict'),
              'amount':fields.float('Amount'),
              'note':fields.char('Note',size=255)
              }
    _defaults={
               'amount':lambda *a:0.0,
               }
kderp_payment_vat_invoice()