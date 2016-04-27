from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
class kderp_other_expense(osv.osv):
    _name = 'kderp.other.expense'
    _inherit= 'kderp.other.expense'      
    
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
        
kderp_other_expense()

