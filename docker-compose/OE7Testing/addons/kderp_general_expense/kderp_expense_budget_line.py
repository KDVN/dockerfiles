from openerp.osv import fields, osv

from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_expense_budget_line(osv.osv):
    _name='kderp.expense.budget.line'
    _inherit='kderp.expense.budget.line'
    
    #Expense Type allocated to budget only Expense and Monthly Expense
    def create_update_expense_budget_line(self,cr,uid,ids,res_obj,field_link='order_id',context={}):
        dict_exp_obj = {'purchase.order':'purchase_order','purchase.order.line':'purchase_order_line',
                        'kderp.other.expense':'kderp_other_expense','kderp.other.expense.line':'kderp_other_expense_line'}
        
        #po_budget_line_ids = []
        pol_link_dicts={}
        for exp in self.pool.get(res_obj).browse(cr,uid,ids,context):
            expense_budget_lines = []
            expense_budget_lines_delete = []
        
            expense_id = exp.id
            
            if res_obj=='purchase.order':
                exp_date = exp.date_order
                exp_type = True
            else:
                exp_date = exp.date
                exp_type = "expense_type in ('expense','monthly_expense')"
            #Expense Type allocated to budget only Expense and Monthly Expense            
            exp_table=dict_exp_obj[res_obj]
             
            cr.execute("""Select 
                                kebl.id
                            from
                                kderp_expense_budget_line kebl
                            left join
                                %s exp on expense_id=exp.id
                            left join
                                %s_line expl on exp.id=expl.%s and kebl.budget_id=expl.budget_id and kebl.account_analytic_id=expl.account_analytic_id 
                            where 
                                expense_obj='%s' and kebl.expense_id=%s and (coalesce(expl.id,0)=0 or exp.state in ('draft','cancel')) or not %s 
                            group by
                                kebl.id,
                                kebl.account_analytic_id,
                                kebl.budget_id
                            Union
                            Select
                                kebl.id
                            from
                                kderp_expense_budget_line kebl
                            left join
                                %s_line expl on kebl.expense_id=expl.%s and kebl.id=expense_budget_line 
                            where 
                                expense_obj='%s' and kebl.expense_id=%s and coalesce(expl.id,0)=0
                                """ % (exp_table,exp_table,field_link,res_obj,expense_id,exp_type,
                                       exp_table,field_link,res_obj,expense_id))
            
            for kebl_id in cr.fetchall():
                expense_budget_lines_delete.append(kebl_id[0])
            if expense_budget_lines_delete:
                deleted_exp=self.unlink(cr, uid, expense_budget_lines_delete,context)
            
            cr.execute("""Select 
                                exp.id as exp_id,
                                expl.account_analytic_id,
                                expl.budget_id
                        from
                            %s exp
                        left join
                            %s_line expl on exp.id=expl.%s
                        left join
                            kderp_expense_budget_line kebl on 
                                                            expense_obj='%s' and 
                                                            exp.id=kebl.expense_id and
                                                            expl.budget_id=kebl.budget_id and 
                                                            expl.account_analytic_id=kebl.account_analytic_id
                        where 
                            exp.state not in ('draft','cancel') and exp.id=%s and coalesce(kebl.id,0)=0 and coalesce(expl.id,0)>0 and %s
                        group by
                            exp.id,
                            expl.account_analytic_id,
                            expl.budget_id""" % (exp_table,exp_table,field_link,res_obj,expense_id,exp_type))
            
            for exp_id,job_id,budget_id in cr.fetchall(): #list need to insert
                    expense_budget_line={'expense_id':exp_id,
                                     'expense_obj':res_obj,
                                     'account_analytic_id':job_id,
                                     'budget_id':budget_id}
                    expense_budget_lines.append(expense_budget_line)
            
            pol_link_dicts={}
            #raise osv.except_osv("E",expense_budget_lines)
            for expense_budget_line in expense_budget_lines:
                expense_budget_line_id=self.create(cr,uid,expense_budget_line,context) #Create Purchase Budget line
        #    expense_budget_line_ids.append(expense_budget_line_id)
                pol_link_dicts[str(expense_budget_line['expense_id'])+str(expense_budget_line['account_analytic_id'])+str(expense_budget_line['budget_id'])]=expense_budget_line_id
            
        return pol_link_dicts    
    
    def action_open_related_obj(self, cr, uid, ids, *args):
        context = filter(lambda arg: type(arg) == type({}), args)
        if not context:
            context = {}
        else:
            context = context[0]

        obj_id=False
        obj=''
        dict_name={'purchase.order':'Purchase Order',
                   'kderp.other.expense':'Other Expense'}        
        
        for object in self.browse(cr, uid, ids):
            obj_id = [object.expense_id]
            obj = object.expense_obj
            
        interface_string = 'General Expense' if context.get('general_expense', False) else dict_name[obj]
        if obj_id:            
            return {
            'type': 'ir.actions.act_window',
            'name': interface_string,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': context,
            'res_model': obj,
            'domain': "[('id','in',%s)]" % obj_id
            }
        else:
            return True
        
    def _get_section(self, cr, uid, ids, name, args, context):
        if not context:
            context = {}
        res = {}
        kebl_ids = []
        expl_obj = self.pool.get('kderp.other.expense.line')
        for kebl in self.browse(cr, uid, ids, context):
            if kebl.expense_obj == 'kderp.other.expense':
                kebl_ids.append(kebl.id)                                
            else:
                res[kebl.id] = False
        if kebl_ids:
            kebl_ids = ','.join(map(str, kebl_ids))
            cr.execute("""Select kebl.id,
                                kotel.section_id
                            from
                                kderp_expense_budget_line kebl
                            left join
                                kderp_other_expense_line kotel on kebl.id = expense_budget_line
                            where
                                kebl.id in (%s)""" % kebl_ids)
            for id, sect_id in cr.fetchall():
                res[id] = sect_id 
        return res
    
    _columns = {
                "section_id":fields.function(_get_section,type='many2one', relation='hr.department', string='Section') 
                }
# 
#     def _get_amount_from_line_and_payment(self, cr, uid, ids, name, args,context={}):
#         if not context:
#             context={}
#         res={}
#         job_obj=self.pool.get('account.analytic.account')
#         kbudget_obj=self.pool.get('kderp.budget.data')
#         list_update=[]
#         kebl_ids=",".join(map(str,ids))
#         cr.execute("""Select
#                             kebl.id,
#                             kebl.budget_id,
#                             kebl.account_analytic_id,
#                             expense_amount as amount,
#                             vwcombine_manual.amount_currency,        
#                             vwcombine_manual.amount_tax,
#                             sum(vwcombine_manual.payment_amount) as payment_amount
#                     from
#                         kderp_expense_budget_line kebl
#                     left join
#                         (Select 
#                             po.id as po_id,
#                             vwpol.budget_id,
#                             vwpol.account_analytic_id,    
#                             amount_currency,
#                             expense_amount,
#                             vwpol.amount_tax,
#                             sum(coalesce(kspl.amount*coalesce(fnpo_compute(ksp.currency_id,company_curr,po.date_order),0))) as payment_amount
#                         from
#                             purchase_order po 
#                         left join
#                             kderp_supplier_payment ksp on po.id=order_id 
#                         left join
#                             (Select 
#                                 order_id,
#                                 budget_id,
#                                 account_analytic_id,
#                                 sum(coalesce(final_subtotal,0)) as amount_currency,
#                                 sum(coalesce(amount_company_curr,0)) as expense_amount,
#                                 sum(coalesce(pol.amount_tax,0)) as amount_tax
#                             from
#                                 purchase_order_line pol
#                             where
#                                     (order_id,
#                                     budget_id,
#                                     account_analytic_id) in (Select kebl.expense_id,kebl.budget_id,kebl.account_analytic_id from kderp_expense_budget_line kebl where expense_obj='purchase.order' and kebl.id in (%s)) 
#                             group by
#                                 budget_id,
#                                 account_analytic_id,
#                                 order_id) vwpol on po.id=vwpol.order_id
#                         left join
#                             kderp_supplier_payment_line kspl on  ksp.id=supplier_payment_id and vwpol.budget_id=kspl.budget_id and vwpol.account_analytic_id=kspl.account_analytic_id
#                         left join
#                             (Select currency_id as company_curr from res_company limit 1) vwtemp on True
#                         where
#                             po.state not in ('draft','cancel','done') and coalesce(vwpol.order_id,0)>0 and ksp.state not in ('draft','cancel') and coalesce(ksp.base_on_line,False)=True
#                         group by
#                             vwpol.budget_id,
#                             vwpol.account_analytic_id,
#                             po.id,
#                             expense_amount,    
#                             vwpol.amount_tax,
#                             amount_currency
#                     Union
#                         Select 
#                             po.id as po_id,
#                             budget_id,
#                             pol.account_analytic_id,        
#                             sum(coalesce(final_subtotal,0)) as amount_currency,
#                             sum(coalesce(amount_company_curr,0)) as expense_amount,
#                             sum(coalesce(pol.amount_tax,0)) as amount_tax,
#                             sum(coalesce(final_subtotal,0)) * payment_per as payment_amount
#                         from
#                             purchase_order po     
#                         left join
#                             purchase_order_line pol on po.id=pol.order_id
#                         left join
#                              (Select 
#                                 po.id as po_id,
#                                 case when coalesce(final_price,0)=0 then 0 else sum(sub_total)/(final_price) end as payment_per
#                             from
#                                 kderp_supplier_payment ksp 
#                             left join
#                                 purchase_order po   on po.id=order_id 
#                             where
#                                     po.state not in ('draft','cancel')  and coalesce(ksp.base_on_line,False)=False and ksp.state not in ('draft','cancel')
#                                 and 
#                                     po.id  in (Select                    
#                                             order_id 
#                                             from 
#                                             kderp_supplier_payment  ksp
#                                             left join
#                                             purchase_order po on order_id=po.id
#                                             where 
#                                             po.id in (Select kebl.expense_id from kderp_expense_budget_line kebl where expense_obj='purchase.order' and kebl.id in (%s)) and
#                                             coalesce(base_on_line,False)=True and  ksp.state not in ('draft','cancel') and po.state not in ('draft','cancel','done'))                            
#                             group by 
#                                 po.id) vwpayment_per on po.id=po_id
#                         where
#                             po.state not in ('draft','cancel') and po.id in (Select kebl.expense_id from kderp_expense_budget_line kebl where expense_obj='purchase.order' and kebl.id in (%s))  and coalesce(po_id,0)>0
#                         group by
#                             budget_id,
#                             pol.account_analytic_id,
#                             po.id,
#                             payment_per) vwcombine_manual on expense_id=po_id and kebl.budget_id=vwcombine_manual.budget_id and kebl.account_analytic_id=vwcombine_manual.account_analytic_id
#                     Where
#                         expense_obj='purchase.order' and coalesce(po_id,0)>0 and kebl.id in (%s) 
#                     Group by
#                         kebl.id,
#                         vwcombine_manual.amount_currency,
#                         expense_amount,
#                         vwcombine_manual.amount_tax
#     Union
#                     Select
#                             kebl.id,
#                             kebl.budget_id,
#                             kebl.account_analytic_id,
#                             sum(coalesce(amount_company_curr,0)) as amount,
#                             sum(coalesce(final_subtotal,0)) as amount_currency,
#                             sum(coalesce(pol.amount_tax,0)) as amount_tax,
#                             sum(coalesce(amount_company_curr,0))*coalesce(payment_percentage,0) as payment_amount
#                         from
#                             kderp_expense_budget_line kebl
#                         left join
#                             purchase_order_line pol on expense_id=order_id and kebl.budget_id=pol.budget_id and kebl.account_analytic_id=pol.account_analytic_id
#                         left join
#                             purchase_order po on pol.order_id=po.id
#                         where
#                             expense_obj='purchase.order' and kebl.id in (%s) and 
#                              (po.state='done' or
#                                 po.id not in (Select                                         
#                                                 order_id 
#                                             from 
#                                                 kderp_supplier_payment 
#                                             left join
#                                                 purchase_order po on order_id=po.id
#                                             where 
#                                                 coalesce(base_on_line,False)=True and po.state not in ('draft','cancel','done'))) 
#                         group by
#                             kebl.id,
#                             po.id
#                         Union
#                         Select
#                             kebl.id,
#                             kebl.budget_id,
#                             kebl.account_analytic_id,
#                             sum(coalesce(amount_company_curr,0)) as amount,
#                             sum(coalesce(koel.amount,0)) as amount_currency,
#                             0 as amount_tax,
#                             sum(coalesce(amount_company_curr,0))* case when koe.expense_type='monthly_expense' then 1.0 else coalesce(payment_percentage,0) end as payment_amount
#                         from
#                             kderp_expense_budget_line kebl
#                         left join
#                             kderp_other_expense_line koel on kebl.expense_id=koel.expense_id and kebl.budget_id=koel.budget_id and kebl.account_analytic_id=koel.account_analytic_id
#                         left join
#                             kderp_other_expense koe on koel.expense_id=koe.id
#                         where
#                             expense_obj='kderp.other.expense' and kebl.id in (%s)
#                         group by
#                             kebl.id,
#                             koe.id""" % (kebl_ids,kebl_ids,kebl_ids,kebl_ids,kebl_ids,kebl_ids))
#         job_list=[]
#         kbd_ids=[]
#         for id,bg_id,job_id,amount,amount_currency,amount_tax,p_amount in cr.fetchall():
#              res[id]={'amount':amount,
#                       'amount_currency':amount_currency,
#                       'amount_tax':amount_tax,
#                       'payment_amount':p_amount
#                               }
#              job_list.append(job_id)
#              kbd_ids.extend(kbudget_obj.search(cr, uid, [('budget_id','=',bg_id),('account_analytic_id','=',job_id)]))
#         if not context.get('stop_write_kebl',False):
#             self.write(cr, uid, ids, {}, {'stop_write_kebl':True})
# #         if job_list:
# #             job_obj.write(cr, uid, list(set(job_list)),{'need_update':True})
# #         if kbd_ids:
# #             kbudget_obj.write(cr, uid, list(set(kbd_ids)),{})
# 
#         return res
#     
# ####Get List ID from Purchase and related Object    
#     def _get_purchase_order(self, cr, uid, ids, context=None):
#         result = []
#         for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
#             for pol in po.order_line:
#                 if pol.expense_budget_line:
#                     result.append(pol.expense_budget_line.id)
#         return list(set(result))
#     
#     def _get_expense_line_from_pol(self, cr, uid, ids, context=None):
#         result = []
#         for pol in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
#             for poll in pol.order_id.order_line:
#                 result.append(poll.expense_budget_line.id)
#         return list(set(result))
#     
#     def _get_budget_line_from_supplier_payment(self, cr, uid, ids, context=None):
#         result = {}
#         ksp_obj = self.pool.get('kderp.supplier.payment')
#         for ksp in ksp_obj.browse(cr, uid, ids):
#             for pol in ksp.order_id.order_line:
#                 if pol.expense_budget_line: 
#                     result[pol.expense_budget_line.id]=True
#         result=list(set(result.keys()))
#         return result
#     
#     def _get_budget_line_from_supplier_payment_line(self, cr, uid, ids, context=None):
#         result = {}
#         ksp_obj = self.pool.get('kderp.supplier.payment.line')
#         for kspl in ksp_obj.browse(cr, uid, ids):
#             for pol in kspl.supplier_payment_id.order_id.order_line:
#                 if pol.expense_budget_line: 
#                     result[pol.expense_budget_line.id]=True
#         result=list(set(result.keys()))
#         return result    
#     
#     def _get_budget_line_from_supplier_payment_pay(self, cr, uid, ids, context=None):
#         result = {}
#         kp_obj = self.pool.get('kderp.supplier.payment.pay')
#         for kp in kp_obj.browse(cr, uid, ids):
#             for pol in kp.supplier_payment_id.order_id.order_line:
#                 if pol.expense_budget_line: 
#                     result[pol.expense_budget_line.id]=True
#         result=list(set(result.keys()))
#         return result
#     
# ###Aread of Other Expense    
#     def _get_other_expense_line_from_koel(self, cr, uid, ids, context=None):
#         result = []
#         for koel in self.pool.get('kderp.other.expense.line').browse(cr, uid, ids, context=context):
#             for koell in koel.expense_id.expense_line: 
#                 result.append(koell.expense_budget_line.id)
#         return list(set(result))
# 
#     def _get_other_expense(self, cr, uid, ids, context=None):
#         result = []
#         for koe in self.pool.get('kderp.other.expense').browse(cr, uid, ids, context=context):
#             for koel in koe.expense_line:
#                 if koel.expense_budget_line:
#                     result.append(koel.expense_budget_line.id)
#         return list(set(result))
#     
#     def _get_budget_line_from_supplier_payment_expense(self, cr, uid, ids, context=None):
#         result = {}
#         kspe_obj = self.pool.get('kderp.supplier.payment.expense')
#         for kspe in kspe_obj.browse(cr, uid, ids):
#             for koel in kspe.expense_id.expense_line:
#                 if koel.expense_budget_line: 
#                     result[koel.expense_budget_line.id]=True
#         result=list(set(result.keys()))
#         return result
#     
#     def _get_budget_line_from_supplier_payment_expense_line(self, cr, uid, ids, context=None):
#         result = {}
#         kspel_obj = self.pool.get('kderp.supplier.payment.expense.line')
#         for ksple in kspel_obj.browse(cr, uid, ids):
#             for koel in ksple.supplier_payment_expense_id.expense_id.expense_line:
#                 if koel.expense_budget_line: 
#                     result[koel.expense_budget_line.id]=True
#         result=list(set(result.keys()))
#         return result
#     
#     def _get_budget_line_from_supplier_payment_expense_pay(self, cr, uid, ids, context=None):
#         result = {}
#         kpe_obj = self.pool.get('kderp.supplier.payment.expense.pay')
#         for kpe in kpe_obj.browse(cr, uid, ids):
#             for koel in kpe.supplier_payment_expense_id.expense_id.expense_line:
#                 if koel.expense_budget_line: 
#                     result[koel.expense_budget_line.id]=True
#         result=list(set(result.keys()))
#         return result
# #####END OF 
#     
#     _columns={              
#              
#               #Fields Function Store
#               'amount_currency': fields.function(_get_amount_from_line_and_payment,type='float',method=True,digits_compute=dp.get_precision('Amount'),string='Amount Currency',
#                                                  multi="_get_amount_from_line",
#                                                 store = {
#                                                         'purchase.order.line': (_get_expense_line_from_pol,  ['amount_company_curr','price_unit','plan_qty'], 40),
#                                                         'purchase.order': (_get_purchase_order, ['pricelist_id','date_order','state','discount_amount'], 40),
#                                                         'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
#                                                         
#                                                         'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 40),
#                                                         'kderp.other.expense':(_get_other_expense, ['date','state','currency_id','taxes_id','expense_type'], 40),
#                                                         #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
#                                                         'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date'], 40),
#                                                         'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 40),
#                                                         'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 40),
#                                                         }),
#               'amount_tax': fields.function(_get_amount_from_line_and_payment,type='float',digits_compute=dp.get_precision('Budget'),method=True,string='Tax Amount',
#                                                 multi="_get_amount_from_line",
#                                                 store = {
#                                                         'purchase.order.line':(_get_expense_line_from_pol, ['amount_tax','taxes_id','amount_company_curr','price_unit','plan_qty'], 25),
#                                                         'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state'], 25),
#                                                         'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
#                                                         
#                                                         'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 40),
#                                                         'kderp.other.expense':(_get_other_expense, ['date','state','currency_id','taxes_id','expense_type'], 40),
#                                                         #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
#                                                         'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date'], 40),
#                                                         'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 40),
#                                                         'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 40),
#                                                         }),
#               
#               'amount': fields.function(_get_amount_from_line_and_payment,type='float',digits_compute=dp.get_precision('Budget'),string='Amount In Company Currency',
#                                                 multi="_get_amount_from_line_and_payment",
#                                                 store = {
#                                                         'purchase.order.line':(_get_expense_line_from_pol, ['amount_company_curr','price_unit','plan_qty'], 40),
#                                                         'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state','pricelist_id','state','taxes_id'], 40),
#                                                         'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
#                                                         'kderp.supplier.payment': (_get_budget_line_from_supplier_payment, ['state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 40),
#                                                         'kderp.supplier.payment.pay': (_get_budget_line_from_supplier_payment_pay, None, 40),
#                                                         
#                                                         'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 40),
#                                                         'kderp.other.expense':(_get_other_expense, ['date','state','currency_id','taxes_id','expense_type'], 40),
#                                                         #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
#                                                         'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date'], 40),
#                                                         'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 40),
#                                                         'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 40),
#                                                         }),
#               #_get_amount_payment
#                'payment_amount': fields.function(_get_amount_from_line_and_payment,type='float',digits_compute=dp.get_precision('Budget'),string='Payment Amount',
#                                                 multi="_get_amount_from_line",
#                                                   store = {
#                                                         'purchase.order.line':(_get_expense_line_from_pol, ['amount_company_curr','price_unit','plan_qty'], 45),
#                                                         'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state','pricelist_id','state','date_order','taxes_id'], 45),
#                                                         'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 45),
#                                                         'kderp.supplier.payment': (_get_budget_line_from_supplier_payment, ['state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date','base_on_line','order_id'], 45),
#                                                         'kderp.supplier.payment.line': (_get_budget_line_from_supplier_payment_line, None, 45),
#                                                         'kderp.supplier.payment.pay': (_get_budget_line_from_supplier_payment_pay, None, 45),
#                                                         
#                                                         'kderp.other.expense.line':(_get_other_expense_line_from_koel, ['amount_company_curr','amount'], 45),
#                                                         'kderp.other.expense':(_get_other_expense, ['date','state','currency_id','taxes_id','expense_type'], 45),
#                                                         #'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 40),
#                                                         'kderp.supplier.payment.expense': (_get_budget_line_from_supplier_payment_expense, ['state','taxes_id','currency_id','date','expense_id'], 45),
#                                                         'kderp.supplier.payment.expense.line': (_get_budget_line_from_supplier_payment_expense_line, ['amount'], 45),
#                                                         'kderp.supplier.payment.expense.pay': (_get_budget_line_from_supplier_payment_expense_pay, None, 45),
# 
#                                                         }),
#               }
# kderp_expense_budget_line()