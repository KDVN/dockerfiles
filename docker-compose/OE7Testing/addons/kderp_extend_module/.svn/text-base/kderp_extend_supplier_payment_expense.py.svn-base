from openerp.osv import fields, osv

class kderp_supplier_payment_expense(osv.osv):
    _name = 'kderp.supplier.payment.expense'
    _inherit= 'kderp.supplier.payment.expense'      
    

    def _onchange_payment_type(self, cr, uid, ids, context=None):
        """    
            Kiem tra user co trong nhom KDERP - Supplier Payment Expense Read Only Bankstransfer, neu trong nhom do thi khong dc doi payment type khac cash
        """
        user_id = self.pool.get('res.users').browse(cr, uid, uid).id
        for kspe in self.browse(cr, uid, ids,  context=context):
            if kspe.payment_type != 'cash':
                cr.execute("""SELECT uid
                              FROM res_groups_users_rel 
                                  where gid in( select id from res_groups where name ='KDERP - Supplier Payment Expense Read Only Bankstransfer');
                            """)
            for user in cr.fetchall():
                    if uid in user :
                        raise osv.except_osv("KDERP Warning",'Cannot change Payment Type')
            return True
    _constraints = [ (_onchange_payment_type, 'Error Input', ['payment_type','usesr_id'])]
   
    
kderp_supplier_payment_expense()

