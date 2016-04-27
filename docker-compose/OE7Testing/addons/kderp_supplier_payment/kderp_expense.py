from osv import osv, fields
from osv.orm import intersect
import time
import openerp.addons.decimal_precision as dp
import openerp.exceptions

class kderp_other_expense(osv.osv):
    _name="kderp.other.expense"
    _inherit='kderp.other.expense'
    _description="Add VAT Invoice and Payment to Other Expense"
    
    def _get_payment_vat_invoices(self, cr, uid, ids,  name, args, context={}):
        if not context:
            context={}
        res={}
        for exp_obj in self.browse(cr, uid, ids, context):        
            res[exp_obj.id]=[]
            for kspe_obj in exp_obj.supplier_payment_expense_ids:
                for ksvi in kspe_obj.kderp_vat_invoice_ids:        
                    res[exp_obj.id].append(ksvi.id)                
        return res

    _columns={
             'supplier_payment_expense_ids':fields.one2many('kderp.supplier.payment.expense','expense_id','Supplier Payment'),             
             'supplier_vat_ids':fields.function(_get_payment_vat_invoices,string='VAT Invoices',
                                                    type='one2many',relation='kderp.supplier.vat.invoice',method=True),
             }
    #Inherit Default ORM
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'supplier_payment_expense_ids': [],
            'supplier_vat_ids': []
        })
        return super(kderp_other_expense, self).copy(cr, uid, id, default, context)
    #Create Payment
    def supplier_payment_detail_create(self,job_id,amount, percent):

        return (0, False, {
            'account_analytic_id':job_id,
            'amount': amount*percent/100.0
        })
        
    def action_expense_create_supplier_payment_expense(self, cr, uid, ids, *args):
        res = {}
        kspe_ids=[]
        for koe in self.browse(cr, uid, ids):
            if koe.supplier_payment_expense_ids:
                return True
            payment_details = []
            progress = 0.0

            payment_details = []
            cr.execute("Select\
                            account_analytic_id,\
                            sum(amount)\
                        from \
                            kderp_other_expense_line koel\
                        where expense_id=%s\
                        group by\
                            koel.account_analytic_id" % (koe.id))
            for job_id,amount in cr.fetchall():
                payment_details.append(self.supplier_payment_detail_create(job_id, amount, 100))
                
            if koe.description:
                new_description = koe.description
            else:
                new_description = ""
            tax_ids=[]
            for tax_id in koe.taxes_id:
                tax_ids.append(tax_id.id)
            payment = {
                'amount':koe.amount_untaxed,
                'taxes_id': [[6, False, tax_ids]],
                'currency_id': koe.currency_id.id,
                'payment_line': payment_details,
                'expense_id':koe.id, 
                'description':new_description#po_term['name'] + "\n"+  o['notes']
                }

            kderp_kspe_id = self.pool.get('kderp.supplier.payment.expense').create(cr, uid, payment)
            kspe_ids.append(kderp_kspe_id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier Payment (OExpense)',
            'view_type': 'form',
            'res_id':kspe_ids[0],
            'target':'current',
            'nodestroy': True,
            'view_mode': 'form,tree',
            'res_model': 'kderp.supplier.payment.expense',
            'domain': "[('id','in',%s)]" % kspe_ids
            }
        
    def action_draft_to_waiting_for_payment(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        todo = []
        period_obj = self.pool.get('account.period')
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.expense_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a Expense without any Expense Details.'))

            period_id = exp.period_id and exp.period_id.id or False
            if not period_id:
                period_ids = period_obj.find(cr, uid, exp.date, context)
                period_id = period_ids and period_ids[0] or False
            self.write(cr, uid, [exp.id], {'state' : 'waiting_for_payment', 'period_id':period_id})
            result = self.action_expense_create_supplier_payment_expense(cr, uid, ids)
        return result
    
    def action_cancel(self, cr, uid, ids, context=None):
        for koe in self.browse(cr, uid, ids):
            for kspe in koe.supplier_payment_expense_ids:
                if kspe.state not in ('draft','cancel'):
                    raise osv.except_osv("KDERP Warning","Please Cancel all Request of Payment Related, before you cancel this PO.")
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
kderp_other_expense()
