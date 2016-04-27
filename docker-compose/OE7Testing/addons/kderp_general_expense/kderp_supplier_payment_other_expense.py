from openerp.osv import fields, osv
    
class kderp_supplier_payment_expense(osv.osv):
    _name = 'kderp.supplier.payment.expense'
    _inherit = 'kderp.supplier.payment.expense'
    _description = 'Supplier Payment for Expense'    
        
    def _get_exrate(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        company_currency = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency=company_currency.id
        res = {}
        for rope in self.browse(cr,uid,ids):
            if rope.currency_id.id == rope.expense_id.currency_id.id and rope.expense_id.manual_exrate:
                res[rope.id] = rope.expense_id.manual_exrate
            else:
                from_curr = rope.currency_id.id
                compute_date = rope.expense_id.date
                res[rope.id] = cur_obj.compute(cr, uid, from_curr, company_currency, 1, round=False,context={'date': compute_date})
        return res               
  
    def _get_sp_expense_from_ot(self, cr, uid, ids, c={}):
        koe_obj = self.pool.get('kderp.other.expense')
        res = {}        
        for koe in koe_obj.browse(cr, uid, ids, c):
            for kspe in koe.supplier_payment_expense_ids:
                res[kspe.id] = True
        return res.keys() 

    _columns={              
              'exrate':fields.function(_get_exrate,type='float', method=True,string='Ex.Rate',
                                       store={
                                              'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['date','currency_id','expense_id'], 10),
                                              'kderp.other.expense': (_get_sp_expense_from_ot, ['date','currency_id','expense_id','manual_exrate'], 10)
                                              }),
            }
kderp_supplier_payment_expense()
