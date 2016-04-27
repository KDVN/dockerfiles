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
    _description='Expense Budget Line'
    
    def action_open_related_obj(self, cr, uid, ids, *args):
        obj_id=False
        obj=''
        dict_name={'purchase.order':'Purchase Order',
                   'kderp.other.expense':'Other Expense'}
        for obj in self.browse(cr, uid, ids):
            obj_id = [obj.expense_id]
            obj=obj.expense_obj
            
        if obj_id:
            return {
            'type': 'ir.actions.act_window',
            'name': dict_name[obj],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': obj,
            'domain': "[('id','in',%s)]" % obj_id
            }
        else:
            return True
        
    
    def create_update_expense_budget_line(self,cr,uid,ids,res_obj,field_link='order_id',context={}):
        dict_exp_obj = {'purchase.order':'purchase_order','purchase.order.line':'purchase_order_line',
                        'kderp.other.expense':'kderp_other_expense','kderp.other.expense.line':'kderp_other_expense_line'}
        
        #po_budget_line_ids = []
        pol_link_dicts={}
        for exp in self.pool.get(res_obj).browse(cr,uid,ids,context):
            expense_budget_lines = []
            expense_budget_lines_delete = []
        
            expense_id = exp.id
            period_id = exp.period_id.id
            if res_obj=='purchase.order':
                exp_date = exp.date_order
            else:
                exp_date = exp.date
                
            exrate = exp.exrate
            exp_currency = exp.currency_id.id
            
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
                                expense_obj='%s' and kebl.expense_id=%s and (coalesce(expl.id,0)=0 or exp.state in ('draft','cancel')) 
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
                                """ % (exp_table,exp_table,field_link,res_obj,expense_id,exp_table,field_link,res_obj,expense_id))
            
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
                            exp.state not in ('draft','cancel') and exp.id=%s and coalesce(kebl.id,0)=0 and coalesce(expl.id,0)>0
                        group by
                            exp.id,
                            expl.account_analytic_id,
                            expl.budget_id""" % (exp_table,exp_table,field_link,res_obj,expense_id))
            
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
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = {}
        #kebl_lsts=[]
        for kebl in self.browse(cr,uid,ids):
            res[kebl.id]=kebl.name
#             kebl_lsts.append([kebl.id,[kebl.expense_id],kebl.expense_obj,kebl.account_analytic_id.code + "-" + kebl.budget_id.code])
#         for lst in kebl_lsts:
#             for exp_obj in self.pool.get(lst[2]).browse(cr, uid, lst[1],context):
#                 name=exp_obj.name
#             res.append((lst[0], name +"-"+ lst[3]))
        return res
    
    def _get_withoutcontract(self, cr, uid, ids, name, args,context={}):
        res={}
        
        dict_obj={'purchase.order':True}
        kbudget_obj=self.pool.get('kderp.budget.data')
        
        for kebl in self.browse(cr, uid, ids, context):
            if kebl.expense_obj in dict_obj:
                res[kebl.id]=self.pool.get(kebl.expense_obj).browse(cr, uid, kebl.expense_id).without_contract
            else:
                res[kebl.id]=True
            kbd_ids=kbudget_obj.search(cr, uid, [('budget_id','=',kebl.budget_id.id),('account_analytic_id','=',kebl.account_analytic_id.id)])
            if kbd_ids:
                kbudget_obj.write(cr, uid, kbd_ids,{})
        return res
    
    def _get_amount_from_line(self, cr, uid, ids, name, args,context={}):
        res={}
        dict_obj={'purchase.order':'purchase_order_line'}
        for kebl in self.browse(cr, uid, ids, context):
            res[kebl.id]={'amount':0.0,
                          'amount_currency':0.0,
                          'amount_tax':0.0}
            
            cr.execute("""Select
                            sum(coalesce(final_subtotal,0)) as amount_currency,
                            sum(coalesce(amount_company_curr,0)) as amount,
                            sum(coalesce(amount_tax,0)) as amount_tax
                        from
                            %s
                        where
                            order_id=%s and budget_id=%s and account_analytic_id=%s 
                        group by
                            order_id,
                            budget_id,
                            account_analytic_id""" % (dict_obj[kebl.expense_obj],kebl.expense_id,kebl.budget_id.id,kebl.account_analytic_id.id))
            for ac,a,at in cr.fetchall():
                res[kebl.id]={'amount':a,
                          'amount_currency':ac,
                          'amount_tax':at}
        return res
        
    def _get_curr_period_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        list_cal = []
        for kebl in self.browse(cr,uid,ids):
            list_cal.append([kebl.id,str(kebl.expense_obj),[kebl.expense_id]])
            res[kebl.id]={'exrate':False,
                     'currency_id':False,
                     'period_id':False,
                     'date':False,
                     'partner_id':False,
                     'description':False,
                     'name':False}

        for lst in list_cal:
            for obj in self.pool.get(lst[1]).browse(cr, uid,lst[2]):
                res[lst[0]]['exrate']=obj.exrate
                res[lst[0]]['currency_id']=obj.currency_id.id
                res[lst[0]]['period_id']=obj.period_id.id if obj.period_id else False
                res[lst[0]]['exrate']=obj.exrate
                res[lst[0]]['name']=obj.name
                res[lst[0]]['partner_id']=obj.partner_id.id
                if lst[1]=='purchase.order':
                    res[lst[0]]['date']=obj.date_order
                    res[lst[0]]['description']=obj.notes
#                 else:
#                     res[lst[0]]['description']=obj.description                
#                     res[lst[0]]['date']=obj.date
        return res
    
    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = []
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for pol in po.order_line:
                if pol.expense_budget_line:
                    result.append(pol.expense_budget_line.id)
        return list(set(result))
    
    def _get_other_expense(self, cr, uid, ids, context=None):
        result = []
        for koe in self.pool.get('kderp.other.expense').browse(cr, uid, ids, context=context):
            for koel in koe.expense_line:
                if koel.expense_budget_line:
                    result.append(koel.expense_budget_line.id)
        return list(set(result))
    
    def _get_expense_line_from_pol(self, cr, uid, ids, context=None):
        result = []
        for pol in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            if pol.expense_budget_line:
                result.append(pol.expense_budget_line.id)
        return list(set(result))
    
    _columns={              
              'expense_id':fields.integer('Expense ID',ondelete="restrict",required=True,select=1),
              'expense_obj':fields.char('Model',size=128,required=True,select=1),
              'budget_id':fields.many2one('account.budget.post',"Budget",select=1),
              'account_analytic_id':fields.many2one('account.analytic.account','Job',required=True,select=1),
              
              #File Function Store
              'without_contract':fields.function(_get_withoutcontract,type='boolean',method=True,string='Without Contract',
                                                store = {
                                                        'purchase.order': (_get_purchase_order, ['without_contract'], 40),
                                                        }),
              
              'amount_currency': fields.function(_get_amount_from_line,type='float',method=True,digits_compute=dp.get_precision('Amount'),string='Amount Currency',
                                                 multi="_get_amount_from_line",
                                                store = {
                                                        'purchase.order.line': (_get_expense_line_from_pol,  ['amount_company_curr','price_unit','plan_qty'], 40),
                                                        'purchase.order': (_get_purchase_order, ['currency_id','date_order','state','discount_amount'], 40),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
                                                        }),
              'amount': fields.function(_get_amount_from_line,type='float',digits_compute=dp.get_precision('Budget'),method=True,string='Amount In Company Currency',
                                                multi="_get_amount_from_line",
                                                store = {
                                                        'purchase.order.line':(_get_expense_line_from_pol, ['price_unit','plan_qty'], 25),
                                                        'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state'], 25),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
                                                        }),
              'amount_tax': fields.function(_get_amount_from_line,type='float',digits_compute=dp.get_precision('Budget'),method=True,string='Tax Amount',
                                                multi="_get_amount_from_line",
                                                store = {
                                                        'purchase.order.line':(_get_expense_line_from_pol, ['amount_tax'], 25),
                                                        'purchase.order':(_get_purchase_order, ['discount_amount','special_case','state'], 25),
                                                        'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 20),
                                                        }),              
              #Related Field

              'exrate':fields.function(_get_curr_period_date, string='Exrate', type='float', multi='kderp_get_id', digits_compute=dp.get_precision('Account'),
                                store = {
                                    'purchase.order':(_get_purchase_order, ['currency_id','pricelist_id','date_order'], 20),
                                 #   'kderp.other.expense':(_get_other_expense, ['currency_id','date'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'partner_id':fields.function(_get_curr_period_date,string='Supplier', type='many2one', relation='res.partner',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['partner_id'], 20),
                                 #   'kderp.other.expense':(_get_other_expense, ['partner_id'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              
              'name':fields.function(_get_curr_period_date,string='Name', type='char',size=32, multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['name'], 20),
                                 #   'kderp.other.expense':(_get_other_expense, ['name'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'description':fields.function(_get_curr_period_date,string='Desc.', type='char',size=256,multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['notes'], 20),
                                    #'kderp.other.expense':(_get_other_expense, ['description'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
                            
              'currency_id':fields.function(_get_curr_period_date,string='Curr.', type='many2one', relation='res.currency',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['currency_id','pricelist_id'], 20),
                                    #'kderp.other.expense':(_get_other_expense, ['currency_id'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'period_id':fields.function(_get_curr_period_date, string='Period', type='many2one', relation='account.period',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['period_id'], 20),
                                  #  'kderp.other.expense':(_get_other_expense, ['period_id'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'date': fields.function(_get_curr_period_date ,string='Date of Order', type='date',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['date_order'], 20),
                                  #  'kderp.other.expense':(_get_other_expense, ['date'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              }
    _sql_constraints = [
        ('unique_expense_job_budget', 'unique(expense_id,expense_obj,budget_id,account_analytic_id)', 'Expense Budget Line must be unique !')
        ]
kderp_expense_budget_line()


class purchase_order_line(osv.osv):
    _name='purchase.order.line'
    _inherit='purchase.order.line'
    _description='Customize Purchase Order line for Kinden'
    _columns={
              'expense_budget_line':fields.many2one('kderp.expense.budget.line','Expense Budget Line',ondelete="set null")
              }
purchase_order_line()