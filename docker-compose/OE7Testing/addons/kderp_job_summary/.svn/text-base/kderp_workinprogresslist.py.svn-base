from openerp.osv.orm import Model
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import re

class kderp_workinprogress_report(Model):
    _name = 'kderp.workinprogress.report'
    _description='KDERP Job Work In Progress Report'
    _auto=False
    
    _columns={             
              #Contracted Info
            'account_analytic_id':fields.many2one('account.analytic.account','Job'),
               
            'material_planned_amount':fields.float('Material Budget Amount'),
            'site_expense_planned_amount':fields.float('Site Expense Budget Amount'),
            'sub_contractor_planned_amount':fields.float('Sub Contractor Budget Amount'),
            'gse_planned_amount':fields.float('GSE Budget Amount'),
            'kfp_planned_amount':fields.float('KFP Budget Amount'),
            'profit_planned_amount':fields.float('Profit Budget Amount'),

            'material_order_amount':fields.float('Material Order'),
            'site_expense_order_amount':fields.float('Site Expense Order'),
            'sub_contractor_order_amount':fields.float('Sub Contractor Order'),
            'gse_order_amount':fields.float('GSE Order'),
            'kfp_order_amount':fields.float('KFP Order'),
            'profit_order_amount':fields.float('Profit Order'),
            
            'material_payment_amount':fields.float('Material Payment'),
            'site_expense_payment_amount':fields.float('Site Expense Payment'),
            'sub_contractor_payment_amount':fields.float('Sub Contractor Payment'),
            'gse_payment_amount':fields.float('GSE Payment'),
            'kfp_payment_amount':fields.float('KFP Payment'),
            'profit_payment_amount':fields.float('Profit Payment')
             }
    def init(self,cr):
        cr.execute("""Create or replace view kderp_workinprogress_report as
                        Select
                            aaa.id,
                            aaa.id as account_analytic_id,
                            coalesce(max(case when category='material' then subtotal else null end),0) as material_planned_amount,
                            coalesce(max(case when category='site_expense' then subtotal else null end),0) as site_expense_planned_amount,
                            coalesce(max(case when category='sub_contractor' then subtotal else null end),0) as sub_contractor_planned_amount,
                            coalesce(max(case when category='gse' then subtotal else null end),0) as gse_planned_amount,
                            coalesce(max(case when category='kfp' then subtotal else null end),0) as kfp_planned_amount,
                            coalesce(max(case when category='profit' then subtotal else null end),0) as profit_planned_amount,
                            
                            sum(case when category='material' then coalesce(kebl.amount,0) else 0 end) as material_order_amount,
                            sum(case when category='site_expense' then coalesce(kebl.amount,0) else 0 end) as site_expense_order_amount,
                            sum(case when category='sub_contractor' then coalesce(kebl.amount,0) else 0 end) as sub_contractor_order_amount,
                            sum(case when category='gse' then coalesce(kebl.amount,0) else 0 end) as gse_order_amount,
                            sum(case when category='kfp' then coalesce(kebl.amount,0) else 0 end) as kfp_order_amount,
                            sum(case when category='profit' then coalesce(kebl.amount,0) else 0 end) as profit_order_amount,
                            
                            sum(case when category='material' then coalesce(payment_amount,0) else 0 end) as material_payment_amount,
                            sum(case when category='site_expense' then coalesce(payment_amount,0) else 0 end) as site_expense_payment_amount,
                            sum(case when category='sub_contractor' then coalesce(payment_amount,0) else 0 end) as sub_contractor_payment_amount,
                            sum(case when category='gse' then coalesce(payment_amount,0) else 0 end) as gse_payment_amount,
                            sum(case when category='kfp' then coalesce(payment_amount,0) else 0 end) as kfp_payment_amount,
                            sum(case when category='profit' then coalesce(payment_amount,0) else 0 end) as profit_payment_amount
                        from 
                            account_analytic_account aaa
                        left join
                            (Select 
                                account_analytic_id,
                                category as category1,
                                sum(coalesce(planned_amount,0)) as subtotal
                            from 
                                kderp_budget_data kbd 
                            left join 
                                vwbudget_category vwbc on kbd.budget_id=vwbc.budget_id
                            group by
                                account_analytic_id,
                                category) vwplanned on aaa.id=vwplanned.account_analytic_id
                        left join
                            vwbudget_category vwbc on vwplanned.category1=vwbc.category
                        left join
                            kderp_expense_budget_line kebl on aaa.id= kebl.account_analytic_id and vwbc.budget_id=kebl.budget_id
                        Group by
                            aaa.id""")
kderp_workinprogress_report()

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit='account.analytic.account'
    _description="KDERP Job Add Work in Progress List"
    
    _columns={
              'workinprogress_ids':fields.one2many('kderp.workinprogress.report','account_analytic_id','Work In Progress',readonly=True)
              } 
account_analytic_account()