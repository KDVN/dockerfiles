from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_budget_data(osv.osv):
    _name = 'kderp.budget.data'
    _inherit = 'kderp.budget.data'
    _description = 'Budget Data for Job (Kinden)'
    
    def open_budget_detail(self, cr, uid, ids, context=None):
        if not context:
            context={}
        return {
            "type": "ir.actions.act_window",
            "name": "Detail of Budget",
            "res_model": "kderp.budget.data",
            "res_id": ids[0] if ids else False,
            "view_type": "form",
            "view_mode": "form",
            'target':'new',
            'nodestroy':True,
            'context':context
        }
        
    def _get_summaryofbudget(self, cr, uid, ids, name, args, context):
        res = {}
        balance_over_budget=self.pool.get('res.users').browse(cr,uid,uid).company_id.over_budget_value
        if ids:
            budget_data_ids = ",".join(map(str,ids))
            cr.execute("""Select 
                            kbd.id,
                            planned_amount,
                            sum(coalesce(amount,0)) as expense_amount,
                            sum(coalesce(payment_amount,0)) as paid_amount,
                            sum(case when coalesce(without_contract,False)=False then coalesce(amount,0) else 0 end) as po_withcontract,
                            sum(case when coalesce(without_contract,False)=True then coalesce(amount,0) else 0 end) as po_withoutcontract                            
                        from 
                            kderp_budget_data kbd 
                        left join 
                            kderp_expense_budget_line kebl on kbd.account_analytic_id=kebl.account_analytic_id and kbd.budget_id = kebl.budget_id
                        where
                            kbd.id in (%s)
                        group by
                            kbd.id""" % budget_data_ids)
                        
            for id, pl_amount, amount, paid_amount, exp_w, exp_wo in cr.fetchall():
                res[id]={'balance_per':amount/pl_amount*100.0 if pl_amount else 0,
                         'over': 'Yes' if (pl_amount-amount)<=balance_over_budget else 'No',
                         'expense_amount':amount,
                         'paid_amount':paid_amount,
                         'expense_without_contract':exp_wo,
                         'expense_with_contract':exp_w,
                         'balance_amt': pl_amount-amount
                         }
        return res
     
    def _get_budget_line_from_job_budget_line(self, cr, uid, ids, context=None):
        res=[]
        for kebl in self.pool.get('kderp.expense.budget.line').browse(cr,uid,ids):
            for kbd in kebl.account_analytic_id.kderp_budget_data_line:
                if kbd.budget_id.id==kebl.budget_id.id:
                    res.append(kbd.id)
        return list(set(res))
    
    def _get_budget_from_company(self, cr, uid, ids, context=None):
        res=[]
        cr.execute('select id from kderp_budget_data')
        for id in cr.fetchall():
            res.append(id[0])
        return res
    
    def _get_detail_budget(self, cr, uid, ids, name, args, context):
        res={}
        kbd_ids=",".join(map(str,ids))
        cr.execute("""Select 
                        kbd.id as kbd_id,
                        trim(array_to_string(array_agg(kebl.id::text),' '))
                    from
                        kderp_budget_data kbd
                    left join
                        kderp_expense_budget_line kebl on kbd.account_analytic_id=kebl.account_analytic_id and kbd.budget_id=kebl.budget_id and coalesce(kebl.id,0)>0
                    where
                         kbd.id in (%s)
                    Group by
                        kbd.id""" % kbd_ids)
          
        for kbd_id,list_id in cr.fetchall():
            tmp_list=list_id
            if not tmp_list:
                tmp_list=[]
            elif tmp_list.isdigit():
                tmp_list=[int(tmp_list)]
            else:
                tmp_list=list(eval(tmp_list.strip().replace(' ',',').replace(' ','')))
            res[kbd_id]=tmp_list
        return res
    
    # Chan xoa budget
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        unlink_ids = []
        for kbd in self.browse(cr, uid, ids, context=context):
            if kbd.detail_budget:
                raise osv.except_osv("KDERP Warning",'Can not DELETE budget having expenses.')
            unlink_ids.append(kbd.id)
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
        
    _columns={
              'expense_amount':fields.function(_get_summaryofbudget,string='Purchased',digits_compute=dp.get_precision('Budget'),method=True,type='float',multi='_get_info',
                                               store={
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50)
                                                     }),              
              'paid_amount':fields.function(_get_summaryofbudget,string='Paid',digits_compute=dp.get_precision('Budget'),method=True,type='float',multi='_get_info',
                                               store={
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50)
                                                     }),              
              'balance_per':fields.function(_get_summaryofbudget,string='Balance (%)',digits_compute=dp.get_precision('Amount'),method=True,type='float',multi='_get_info',
                                               store={
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50)
                                                      }),
              'over':fields.function(_get_summaryofbudget,string='Over',method=True,type='char',size=8,multi='_get_info',
                                               store={
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50),
                                                     'res.company':(_get_budget_from_company,['over_budget_value'],50)
                                                     }),
              
              'expense_without_contract':fields.function(_get_summaryofbudget,string='Amt. Without Contract',method=True,type='float',digits_compute=dp.get_precision('Budget'),size=8,multi='_get_info',
                                               store={
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50)
                                                     }),
              'expense_with_contract':fields.function(_get_summaryofbudget,string='Amt. With Contract',method=True,type='float',digits_compute=dp.get_precision('Budget'),multi='_get_info',
                                               store={
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50)
                                                      }),
              'balance_amt':fields.function(_get_summaryofbudget,string='Balance',digits_compute=dp.get_precision('Budget'),method=True,type='float',multi='_get_info',
                                                store={
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50),
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                      }),
              'detail_budget':fields.function(_get_detail_budget,method=True,type='one2many',relation='kderp.expense.budget.line')
                            
              }
    _defaults={
               'expense_amount': lambda *x: 0.0,
               'paid_amount': lambda *x: 0.0,
               'balance_per': lambda *x: 0.0,
               'over': lambda *x:'No',
               'expense_without_contract':lambda *x:0.0,
               'expense_with_contract':lambda *x:0.0,
               'balance_amt':lambda *x:0.0
               }    
kderp_budget_data()