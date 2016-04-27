import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_expense_budget_line(osv.osv):
    _name='kderp.expense.budget.line'
    _inherit = 'kderp.expense.budget.line'
    _description='Expense Budget Line'
    
    def _get_amount_payment1(self, cr, uid, ids, name, args,context={}):
        res={}
        dict_obj={'purchase.order':'purchase_order_line',
                  'kderp.other.expense':'kderp_other_expense_line'}
        kebl_ids=','.join(map(str,ids))
        cr.execute("""Select
                        kebl.id,
                        coalesce(kebl.amount*payment_percentage,0) as payment_amount
                    from
                        kderp_expense_budget_line kebl
                    left join
                        purchase_order po on kebl.expense_id=po.id and kebl.expense_obj='purchase.order'
                    where kebl.expense_obj='purchase.order' and kebl.id in (%s)
                    Union
                    Select
                        kebl.id,
                        coalesce(kebl.amount*payment_percentage,0) as payment_amount
                    from
                        kderp_expense_budget_line kebl
                    left join
                        kderp_other_expense koe on kebl.expense_id=koe.id and kebl.expense_obj='kderp.other.expense'
                    where kebl.expense_obj='kderp.other.expense' and kebl.id in (%s)""" % (kebl_ids,kebl_ids))
        for id,pamount in cr.fetchall():
            res[id]=pamount
#         for kebl in self.browse(cr, uid, ids, context):
#             exp_obj = self.pool.get(kebl.expense_obj)
#             payment_per = exp_obj.read(cr, uid, kebl.expense_id,['payment_percentage'])['payment_percentage']
#             res[kebl.id]=kebl.amount*payment_per
        return res
    
    def _get_amount_from_line_and_payment(self, cr, uid, ids, name, args,context={}):
        if not context:
            context={}
        res={}
        job_obj=self.pool.get('account.analytic.account')
        kbudget_obj=self.pool.get('kderp.budget.data')
        list_update=[]
        kebl_ids=",".join(map(str,ids))
        cr.execute("""Select
                            kebl.id,
                            kebl.budget_id,
                            kebl.account_analytic_id,
                            expense_amount as amount,
                            vwcombine_manual.amount_currency,        
                            vwcombine_manual.amount_tax,
                            sum(vwcombine_manual.payment_amount) as payment_amount
                    from
                        kderp_expense_budget_line kebl
                    left join
                        (Select 
                            po.id as po_id,
                            vwpol.budget_id,
                            vwpol.account_analytic_id,    
                            amount_currency,
                            expense_amount,
                            vwpol.amount_tax,
                            sum(coalesce(kspl.amount*coalesce(fnpo_compute(ksp.currency_id,company_curr,po.date_order),0))) as payment_amount
                        from
                            purchase_order po 
                        left join
                            kderp_supplier_payment ksp on po.id=order_id 
                        left join
                            (Select 
                                order_id,
                                budget_id,
                                account_analytic_id,
                                sum(coalesce(final_subtotal,0)) as amount_currency,
                                sum(coalesce(amount_company_curr,0)) as expense_amount,
                                sum(coalesce(pol.amount_tax,0)) as amount_tax
                            from
                                purchase_order_line pol
                            where
                                    (order_id,
                                    budget_id,
                                    account_analytic_id) in (Select kebl.expense_id,kebl.budget_id,kebl.account_analytic_id from kderp_expense_budget_line kebl where expense_obj='purchase.order' and kebl.id in (%s)) 
                            group by
                                budget_id,
                                account_analytic_id,
                                order_id) vwpol on po.id=vwpol.order_id
                        left join
                            kderp_supplier_payment_line kspl on  ksp.id=supplier_payment_id and vwpol.budget_id=kspl.budget_id and vwpol.account_analytic_id=kspl.account_analytic_id
                        left join
                            (Select currency_id as company_curr from res_company limit 1) vwtemp on True
                        where
                            po.state not in ('draft','cancel','done') and coalesce(vwpol.order_id,0)>0 and ksp.state not in ('draft','cancel') and coalesce(ksp.base_on_line,False)=True
                        group by
                            vwpol.budget_id,
                            vwpol.account_analytic_id,
                            po.id,
                            expense_amount,    
                            vwpol.amount_tax,
                            amount_currency
                    Union
                        Select 
                            po.id as po_id,
                            budget_id,
                            pol.account_analytic_id,        
                            sum(coalesce(final_subtotal,0)) as amount_currency,
                            sum(coalesce(amount_company_curr,0)) as expense_amount,
                            sum(coalesce(pol.amount_tax,0)) as amount_tax,
                            sum(coalesce(final_subtotal,0)) * payment_per as payment_amount
                        from
                            purchase_order po     
                        left join
                            purchase_order_line pol on po.id=pol.order_id
                        left join
                             (Select 
                                po.id as po_id,
                                case when coalesce(final_price,0)=0 then 0 else sum(sub_total)/(final_price) end as payment_per
                            from
                                kderp_supplier_payment ksp 
                            left join
                                purchase_order po   on po.id=order_id 
                            where
                                    po.state not in ('draft','cancel')  and coalesce(ksp.base_on_line,False)=False and ksp.state not in ('draft','cancel')
                                and 
                                    po.id  in (Select                    
                                            order_id 
                                            from 
                                            kderp_supplier_payment  ksp
                                            left join
                                            purchase_order po on order_id=po.id
                                            where 
                                            po.id in (Select kebl.expense_id from kderp_expense_budget_line kebl where expense_obj='purchase.order' and kebl.id in (%s)) and
                                            coalesce(base_on_line,False)=True and  ksp.state not in ('draft','cancel') and po.state not in ('draft','cancel','done'))                            
                            group by 
                                po.id) vwpayment_per on po.id=po_id
                        where
                            po.state not in ('draft','cancel') and po.id in (Select kebl.expense_id from kderp_expense_budget_line kebl where expense_obj='purchase.order' and kebl.id in (%s))  and coalesce(po_id,0)>0
                        group by
                            budget_id,
                            pol.account_analytic_id,
                            po.id,
                            payment_per) vwcombine_manual on expense_id=po_id and kebl.budget_id=vwcombine_manual.budget_id and kebl.account_analytic_id=vwcombine_manual.account_analytic_id
                    Where
                        expense_obj='purchase.order' and coalesce(po_id,0)>0 and kebl.id in (%s) 
                    Group by
                        kebl.id,
                        vwcombine_manual.amount_currency,
                        expense_amount,
                        vwcombine_manual.amount_tax
    Union
                    Select
                            kebl.id,
                            kebl.budget_id,
                            kebl.account_analytic_id,
                            sum(coalesce(amount_company_curr,0)) as amount,
                            sum(coalesce(final_subtotal,0)) as amount_currency,
                            sum(coalesce(pol.amount_tax,0)) as amount_tax,
                            sum(coalesce(amount_company_curr,0))*coalesce(payment_percentage,0) as payment_amount
                        from
                            kderp_expense_budget_line kebl
                        left join
                            purchase_order_line pol on expense_id=order_id and kebl.budget_id=pol.budget_id and kebl.account_analytic_id=pol.account_analytic_id
                        left join
                            purchase_order po on pol.order_id=po.id
                        where
                            expense_obj='purchase.order' and kebl.id in (%s) and 
                             (po.state='done' or
                                po.id not in (Select                                         
                                                order_id 
                                            from 
                                                kderp_supplier_payment 
                                            left join
                                                purchase_order po on order_id=po.id
                                            where 
                                                coalesce(base_on_line,False)=True and po.state not in ('draft','cancel','done'))) 
                        group by
                            kebl.id,
                            po.id
                        Union
                        Select
                            kebl.id,
                            kebl.budget_id,
                            kebl.account_analytic_id,
                            sum(coalesce(amount_company_curr,0)) as amount,
                            sum(coalesce(koel.amount,0)) as amount_currency,
                            0 as amount_tax,
                            sum(coalesce(amount_company_curr,0))*coalesce(payment_percentage,0) as payment_amount
                        from
                            kderp_expense_budget_line kebl
                        left join
                            kderp_other_expense_line koel on kebl.expense_id=koel.expense_id and kebl.budget_id=koel.budget_id and kebl.account_analytic_id=koel.account_analytic_id
                        left join
                            kderp_other_expense koe on koel.expense_id=koe.id
                        where
                            expense_obj='kderp.other.expense' and kebl.id in (%s)
                        group by
                            kebl.id,
                            koe.id""" % (kebl_ids,kebl_ids,kebl_ids,kebl_ids,kebl_ids,kebl_ids))
        job_list=[]
        kbd_ids=[]
        for id,bg_id,job_id,amount,amount_currency,amount_tax,p_amount in cr.fetchall():
             res[id]={'amount':amount,
                      'amount_currency':amount_currency,
                      'amount_tax':amount_tax,
                      'payment_amount':p_amount
                              }
             job_list.append(job_id)
             kbd_ids.extend(kbudget_obj.search(cr, uid, [('budget_id','=',bg_id),('account_analytic_id','=',job_id)]))
        if not context.get('stop_write_kebl',False):
            self.write(cr, uid, ids, {}, {'stop_write_kebl':True})
#         if job_list:
#             job_obj.write(cr, uid, list(set(job_list)),{'need_update':True})
#         if kbd_ids:
#             kbudget_obj.write(cr, uid, list(set(kbd_ids)),{})

        return res


    def _get_amount_from_line_and_payment_bak(self, cr, uid, ids, name, args,context={}):
        res={}
        dict_obj={'purchase.order':'purchase_order_line',
                  'kderp.other.expense':'kderp_other_expense',
                  'kderp.other.expense.line':'kderp_other_expense_line'}
        job_obj=self.pool.get('account.analytic.account')
        kbudget_obj=self.pool.get('kderp.budget.data')
        list_update=[]

        for kebl in self.browse(cr, uid, ids, context):
            res[kebl.id]={'amount':0,
                          'amount_currency':0,
                          'amount_tax':0}
            if kebl.expense_obj=='purchase.order':
                cr.execute("""Select
                                sum(coalesce(amount_company_curr,0)) as amount,
                                sum(coalesce(final_subtotal,0)) as amount_currency,
                                sum(coalesce(amount_tax,0)) as amount_tax
                            from
                                %s
                            where
                                order_id=%s and budget_id=%s and account_analytic_id=%s 
                            group by
                                order_id,
                                budget_id,
                                account_analytic_id""" % (dict_obj[kebl.expense_obj],kebl.expense_id,kebl.budget_id.id,kebl.account_analytic_id.id))
            else:
                cr.execute("""Select
                                sum(coalesce(amount_company_curr,0)) as amount,
                                sum(coalesce(amount,0)) as amount_currency,
                                0 as amount_tax
                            from
                                %s
                            where
                                expense_id=%s and budget_id=%s and account_analytic_id=%s 
                            group by
                                expense_id,
                                budget_id,
                                account_analytic_id""" % (dict_obj[kebl.expense_obj+'.line'],kebl.expense_id,kebl.budget_id.id,kebl.account_analytic_id.id))
            if cr.rowcount:
                list_update.append((kebl.account_analytic_id.id,kebl.budget_id.id))
            for amount,amount_curr,at in cr.fetchall():
                res[kebl.id]={'amount':amount,
                              'amount_currency':amount_curr,
                              'amount_tax':at
                              }

        job_list=[]
        kbd_ids=[]
         
        for lst in list(set(list_update)):
            job_list.append(lst[0])
            kbd_ids.extend(kbudget_obj.search(cr, uid, [('budget_id','=',lst[1]),('account_analytic_id','=',lst[0])]))
 
        if job_list:
            job_obj.write(cr, uid, list(set(job_list)),{'need_update':True})
        if kbd_ids:
            kbudget_obj.write(cr, uid, list(set(kbd_ids)),{})
            
        return res
    
####Get List ID from Purchase and related Object    
    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = []
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for pol in po.order_line:
                if pol.expense_budget_line:
                    result.append(pol.expense_budget_line.id)
        return list(set(result))
    
    def _get_expense_line_from_pol(self, cr, uid, ids, context=None):
        result = []
        for pol in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            for poll in pol.order_id.order_line:
                result.append(poll.expense_budget_line.id)
        return list(set(result))
    
    def _get_budget_line_from_supplier_payment(self, cr, uid, ids, context=None):
        result = {}
        ksp_obj = self.pool.get('kderp.supplier.payment')
        for ksp in ksp_obj.browse(cr, uid, ids):
            for pol in ksp.order_id.order_line:
                if pol.expense_budget_line: 
                    result[pol.expense_budget_line.id]=True
        result = result.keys()
        return result
    
    def _get_budget_line_from_supplier_payment_line(self, cr, uid, ids, context=None):
        result = {}
        ksp_obj = self.pool.get('kderp.supplier.payment.line')
        for kspl in ksp_obj.browse(cr, uid, ids):
            for pol in kspl.supplier_payment_id.order_id.order_line:
                if pol.expense_budget_line: 
                    result[pol.expense_budget_line.id]=True
        result=list(set(result.keys()))
        return result    
    
    def _get_budget_line_from_supplier_payment_pay(self, cr, uid, ids, context=None):
        result = {}
        kp_obj = self.pool.get('kderp.supplier.payment.pay')
        for kp in kp_obj.browse(cr, uid, ids):
            for pol in kp.supplier_payment_id.order_id.order_line:
                if pol.expense_budget_line: 
                    result[pol.expense_budget_line.id]=True
        result=list(set(result.keys()))
        return result
    
###Aread of Other Expense    
    def _get_other_expense_line_from_koel(self, cr, uid, ids, context=None):
        result = []
        for koel in self.pool.get('kderp.other.expense.line').browse(cr, uid, ids, context=context):
            for koell in koel.expense_id.expense_line: 
                result.append(koell.expense_budget_line.id)
        return list(set(result))

    def _get_other_expense(self, cr, uid, ids, context=None):
        result = []
        for koe in self.pool.get('kderp.other.expense').browse(cr, uid, ids, context=context):
            for koel in koe.expense_line:
                if koel.expense_budget_line:
                    result.append(koel.expense_budget_line.id)
        return list(set(result))
    
    def _get_budget_line_from_supplier_payment_expense(self, cr, uid, ids, context=None):
        result = {}
        kspe_obj = self.pool.get('kderp.supplier.payment.expense')
        for kspe in kspe_obj.browse(cr, uid, ids):
            for koel in kspe.expense_id.expense_line:
                if koel.expense_budget_line: 
                    result[koel.expense_budget_line.id]=True
        result=list(set(result.keys()))
        return result
    
    def _get_budget_line_from_supplier_payment_expense_line(self, cr, uid, ids, context=None):
        result = {}
        kspel_obj = self.pool.get('kderp.supplier.payment.expense.line')
        for ksple in kspel_obj.browse(cr, uid, ids):
            for koel in ksple.supplier_payment_expense_id.expense_id.expense_line:
                if koel.expense_budget_line: 
                    result[koel.expense_budget_line.id]=True
        result=list(set(result.keys()))
        return result
    
    def _get_budget_line_from_supplier_payment_expense_pay(self, cr, uid, ids, context=None):
        result = {}
        kpe_obj = self.pool.get('kderp.supplier.payment.expense.pay')
        for kpe in kpe_obj.browse(cr, uid, ids):
            for koel in kpe.supplier_payment_expense_id.expense_id.expense_line:
                if koel.expense_budget_line: 
                    result[koel.expense_budget_line.id]=True
        result=list(set(result.keys()))
        return result
#####END OF 
    
    _columns={              
             
              #Fields Function Store
              'amount_currency': fields.function(_get_amount_from_line_and_payment,type='float',method=True,digits_compute=dp.get_precision('Amount'),string='Amount Currency',
                                                 multi="_get_amount_from_line",
                                                store = {
                                                        'purchase.order.line': (_get_expense_line_from_pol,  ['amount_company_curr','price_unit','plan_qty'], 40),
                                                        'purchase.order': (_get_purchase_order, ['pricelist_id','date_order','state','discount_amount'], 40),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
                                                        
                                                        'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 40),
                                                        'kderp.other.expense':(_get_other_expense, ['date','currency_id','state','taxes_id'], 40),
                                                        #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
                                                        'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date'], 40),
                                                        'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 40),
                                                        'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 40),
                                                        }),
              'amount_tax': fields.function(_get_amount_from_line_and_payment,type='float',digits_compute=dp.get_precision('Budget'),method=True,string='Tax Amount',
                                                multi="_get_amount_from_line",
                                                store = {
                                                        'purchase.order.line':(_get_expense_line_from_pol, ['amount_tax','taxes_id','amount_company_curr','price_unit','plan_qty'], 25),
                                                        'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state'], 25),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
                                                        
                                                        'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 40),
                                                        'kderp.other.expense':(_get_other_expense, ['date','currency_id','state','taxes_id'], 40),
                                                        #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
                                                        'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date'], 40),
                                                        'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 40),
                                                        'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 40),
                                                        }),
              
              'amount': fields.function(_get_amount_from_line_and_payment,type='float',digits_compute=dp.get_precision('Budget'),string='Amount In Company Currency',
                                                multi="_get_amount_from_line_and_payment",
                                                store = {
                                                        'purchase.order.line':(_get_expense_line_from_pol, ['amount_company_curr','price_unit','plan_qty'], 40),
                                                        'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state','pricelist_id','taxes_id'], 40),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
                                                        'kderp.supplier.payment': (_get_budget_line_from_supplier_payment, ['state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 40),
                                                        'kderp.supplier.payment.pay': (_get_budget_line_from_supplier_payment_pay, None, 40),
                                                        
                                                        'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 40),
                                                        'kderp.other.expense':(_get_other_expense, ['date','state','currency_id','taxes_id'], 40),
                                                        #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
                                                        'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date'], 40),
                                                        'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 40),
                                                        'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 40),
                                                        }),
              #_get_amount_payment
               'payment_amount': fields.function(_get_amount_from_line_and_payment,type='float',digits_compute=dp.get_precision('Budget'),string='Payment Amount',
                                                multi="_get_amount_from_line",
                                                  store = {
                                                        'purchase.order.line':(_get_expense_line_from_pol, ['amount_company_curr','price_unit','plan_qty'], 45),
                                                        'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state','pricelist_id','date_order','taxes_id'], 45),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 45),
                                                        'kderp.supplier.payment': (_get_budget_line_from_supplier_payment, ['state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date','base_on_line','order_id'], 45),
                                                        'kderp.supplier.payment.line': (_get_budget_line_from_supplier_payment_line, None, 45),
                                                        'kderp.supplier.payment.pay': (_get_budget_line_from_supplier_payment_pay, None, 45),
                                                        
                                                        'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 45),
                                                        'kderp.other.expense':(_get_other_expense, ['date','state','currency_id','taxes_id'], 45),
                                                        #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
                                                        'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date','expense_id'], 45),
                                                        'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 45),
                                                        'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 45),

                                                        }),
              }
kderp_expense_budget_line()
