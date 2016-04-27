from openerp.osv import fields, osv
import time
import datetime
class kderp_general_expense_supplier_payment_pay(osv.osv):
    _name='kderp.general.expense.supplier.payment.pay'
    _description='KDERP General Expense Supplier Payment'
    
    def create(self, cr, uid, vals, context={}):
        new_payment_id = super(kderp_general_expense_supplier_payment_pay, self).create(cr, uid, vals, context=context)
        new_payment_ids=new_payment_id
        if type(new_payment_ids).__name__<>'list':
            new_payment_ids=[new_payment_ids]
        list_failed=[]
        list_gep={}
        ksgesp_ids=[]
        for kp in self.browse(cr, uid, new_payment_ids):
            if kp.general_expense_payment_id.state<>'waiting_for_payment' and  kp.general_expense_payment_id.state<>'revising':
                list_failed.append(kp.general_expense_payment_id.name)
            else:
                ksgesp_ids.append(kp.general_expense_payment_id.id)
        if list_failed:
            raise osv.except_osv("KDVN Error","State of payment must be BOD Approved !\n%s" % str(list_failed))
        ksgesp_obj=self.pool.get('kderp.general.expense.supplier.payment')
        for ksgesp_id in ksgesp_ids:
            ksgesp_obj.write(cr, uid, [ksgesp_id],{'state':'done'})
        if kp.general_expense_payment_id.general_expense_id.state=='waiting_for_payment' and kp.general_expense_payment_id.general_expense_id.type=='others':
            cr.execute("""select kge.id ,sum(qr.total_vat),sum(qr.total_payment),kge.total  
                            from 
                                kderp_general_expense kge
                            left join (
                                        select kgesp.general_expense_id as id ,             
                                                sum(ksvi.total_amount) as total_vat,
                                                kgesp.total as total_payment
                                        from 
                                            kderp_general_expense_supplier_payment kgesp 
                                        left join 
                                            kderp_supplier_payment_genral_expense_vat_invoice_rel kgespinvon on kgesp.id=kgespinvon.payment_general_expense_id
                                        left join 
                                            kderp_supplier_vat_invoice ksvi on ksvi.id = kgespinvon.vat_invoice_id
                                        group by kgesp.general_expense_id,kgesp.id        
                                    )qr   on qr.id = kge.id
                            where kge.id =%s group by kge.id
                               """ % kp.general_expense_payment_id.general_expense_id.id)
            for id,total_vat,total_payment ,total_ge in cr.fetchall():
                if total_vat==total_payment and total_vat==total_ge:
                    cr.execute("""Update kderp_general_expense set state='done' where id = %s """ % kp.general_expense_payment_id.general_expense_id.id)
        return new_payment_id
    
    _columns={
                'date':fields.date(' Date',required=1),
                'bank_id':fields.many2one('res.bank','Bank'),
                'general_expense_payment_id':fields.many2one('kderp.general.expense.supplier.payment','General Expense Supplier Payment',domain="[('state','=','done')]",required=True,)
    
                }
    
kderp_general_expense_supplier_payment_pay()