from osv import osv, fields
from osv.orm import intersect
from openerp import netsvc

import time
import openerp.addons.decimal_precision as dp
import openerp.exceptions

#Red Invoice
class purchase_order(osv.osv):
    _name="purchase.order"
    _inherit='purchase.order'
    _description="Add VAT Invoice and Payment to PO"
    
    def _get_payment_vat_invoices(self, cr, uid, ids,  name, args, context={}):
        if not context:
            context={}
        res={}
        for po_obj in self.browse(cr, uid, ids, context):        
            res[po_obj.id]=[]
            for ksp_obj in po_obj.supplier_payment_ids:
                for ksvi in ksp_obj.kderp_vat_invoice_ids:        
                    res[po_obj.id].append(ksvi.id)                    
        return res

    _columns={             
#              'supplier_payment_ids':fields.function(_get_payment_vat_invoices,string='Supplier Payment',
#                                                     type='one2many',relation='kderp.supplier.payment',method=True
#                                                     ,multi='_get_payment_vat'),
            'supplier_payment_ids':fields.one2many('kderp.supplier.payment','order_id','Supplier Payment'),
            'supplier_vat_ids':fields.function(_get_payment_vat_invoices,string='VAT Invoices',
                                                   type='one2many',relation='kderp.supplier.vat.invoice',method=True),
             }
    #Inherit Default ORM
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'supplier_payment_ids': [],
            'supplier_vat_ids': []
        })
        return super(purchase_order, self).copy(cr, uid, id, default, context)
    
    #Create Payment
    def supplier_payment_detail_create(self,job_id,amount, percent):

        return (0, False, {
            'account_analytic_id':job_id,
            'amount': amount*percent/100.0
        })
        
    def action_expense_create_supplier_payment(self, cr, uid, ids, *args):
        res = {}
        #for o in self.browse(cr, uid, ids):
        ksp_ids=[]
        for po in self.browse(cr, uid, ids):
            payment_details = []
            adv_amount = 0.0
            retention_amount = 0.0
            adv = 0.0
            retention = 0.0
            progress = 0.0
            for po_term in po.purchase_payment_term_ids:
                if po_term.type=='adv':
                    adv_amount = po_term.value_amount*po.final_price/100.0
                    adv = po_term.value_amount
                elif po_term.type=='re':
                    retention_amount = po_term.value_amount*po.final_price/100.0
                    retention = po_term.value_amount
                else:                    
                    progress = po_term.value_amount
            for po_term in po.purchase_payment_term_ids:
                if po_term.type<>'p':
                    this_tax_amount = 0.0
                    this_progress_amount = 0.0
                    if po_term.type=='adv':
                        this_retention_amount = 0.0
                        this_adv_amount = adv_amount
                    else:
                        this_adv_amount = 0.0
                        this_retention_amount = retention_amount
                else:
                    progress = po_term.value_amount
                    this_tax_amount = po.amount_tax*po_term.value_amount/100.0
                    this_progress_amount = po.final_price*po_term.value_amount/100.0
                    this_adv_amount = - adv_amount*progress/100.0
                    this_retention_amount = - retention_amount*progress/100.0
                payment_details = []
                cr.execute("Select\
                                pol.account_analytic_id,\
                                sum(final_subtotal)\
                            from \
                                purchase_order_line pol\
                            where order_id=%s\
                            group by\
                                pol.account_analytic_id" % (po.id))
                for job_id,amount in cr.fetchall():
                    payment_details.append(self.supplier_payment_detail_create(job_id, amount, po_term.value_amount))
                    
                if po.notes:
                    new_description = po_term.name + "\n" + po.notes
                else:
                    new_description = ""
                
                tax_ids=[]
                for tax_id in po.taxes_id:
                    if (tax_id.type=='percent' or po_term.value_amount==100) and po_term.type=='p':
                        tax_ids.append(tax_id.id)
                                                             
                payment = {
                    'amount':this_progress_amount,
                    'taxes_id':[[6, False, tax_ids]],
                    'advanced_amount':this_adv_amount,
                    'retention_amount':this_retention_amount,
                    'currency_id': po.currency_id.id,
                    'payment_line': payment_details,
                    'order_id':po.id, 
                    'description':new_description#po_term['name'] + "\n"+  o['notes']
                    }

                kderp_ksp_id = self.pool.get('kderp.supplier.payment').create(cr, uid, payment)
                ksp_ids.append(kderp_ksp_id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier Payment',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kderp.supplier.payment',
            'domain': "[('order_id','in',%s)]" % ids
            }
    
    def action_cancel(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids):
            for ksp in po.supplier_payment_ids:
                if ksp.state not in ('draft','cancel'):
                    raise osv.except_osv("KDERP Warning","Please Cancel all Request of Payment Related, before you cancel this PO.")
        self.write(cr, uid, ids, {'state':'cancel'})
        wf_service = netsvc.LocalService("workflow")
        for po_id in ids:
            try:
                wf_service.trg_delete(uid, 'purchase.order', po_id, cr)
            except:
                continue
        return True
    
purchase_order()
