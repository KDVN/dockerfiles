from openerp.osv import fields, osv

class kderp_supplier_payment_expense(osv.osv):
    _name = 'kderp.supplier.payment.expense'
    _inherit= 'kderp.supplier.payment.expense'      
    

    def _onchange_banktransfer(self, cr, uid, ids, context=None):
        """
          
        """
        user_id = self.pool.get('res.users').browse(cr, uid, uid).id
        for ksp in self.browse(cr, uid, ids,  context=context):
            cr.execute("""SELECT uid
                              FROM res_groups_users_rel 
                                  where gid in( select id from res_groups where name ='KDERP - Supplier Payment Read Only Bankstransfer');
                            """)
            for user in cr.fetchall():
                    if user_id in user:
                        if  kspe.payment_type != 'cash': 
                            raise osv.except_osv("KDERP Warning",'Cannot change Payment Type')
                    return True
    _constraints = [ (_onchange_banktransfer, 'Error Input', ['payment_type','user_id'])]
   
    
kderp_supplier_payment_expense()

