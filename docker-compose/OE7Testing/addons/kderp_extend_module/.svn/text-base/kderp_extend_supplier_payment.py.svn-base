from openerp.osv import fields, osv

class kderp_supplier_payment(osv.osv):
    _name = 'kderp.supplier.payment'
    _inherit= 'kderp.supplier.payment'      
    
    def _check_cash(self, cr, uid, ids, context=None):
        """
        Kiem tra VAT Invoice khi o trang thai Cash Payment
        """
        var_comp = self.pool.get('res.users').browse(cr, uid, uid).company_id
        payment_bycash_limit = var_comp.payment_bycash_limit
        cash_limit_active = var_comp.payment_bycash_limit
        date_apply = var_comp.date_apply
        
        if not context:
            context={}
        if cash_limit_active:
            for ksp in self.browse(cr, uid, ids, context=context):
                if  ksp.payment_type == 'cash':
                    for var in ksp.kderp_vat_invoice_ids:
                        if var.equivalent_vnd > payment_bycash_limit and var.date > date_apply:
                            raise osv.except_osv("KDERP Warning",'Please check VAT Amount, Total Amount exceeded %s'  %("{:,}".format(int(payment_bycash_limit))))
        return True
    def _onchange_banktransfer(self, cr, uid, ids, context=None):
        """
          Kiem tra user co trong nhom KDERP - Supplier Payment Read Only Bankstransfer, neu trong nhom do thi khong dc doi payment type khac cash
        """
        #user_id = self.pool.get('res.users').browse(cr, uid, uid).id
        for ksp in self.browse(cr, uid, ids,  context=context):
            if ksp.payment_type != 'cash':
                cr.execute("""SELECT uid
                              FROM res_groups_users_rel 
                                  where gid in( select id from res_groups where name ='KDERP - Supplier Payment Read Only Bankstransfer')
                            """)
                for user in cr.fetchall():
                    if uid in user :
                        raise osv.except_osv("KDERP Warning",'Cannot change Payment Type')
            return True
    _constraints = [ (_check_cash, 'Error Input', ['payment_type', 'kderp_vat_invoice_ids', 'date_apply', 'cash_limit_active'])]
    _constraints = [ (_onchange_banktransfer, 'Error Input',['payment_type','usesr_id'])]
   
    _defaults = {  
            
                'payment_type':lambda *a: 'cash',
                
                }
kderp_supplier_payment()

