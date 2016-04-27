from openerp.osv.orm import Model
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
import re

class account_analytic_account(Model):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description='KDERP Project add Contract Info'
    
    def _get_job_cost_info(self, cr, uid, ids, name, arg, context=None):
        res={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_currency = user.company_id.currency_id
        company_currency_id = user.company_id.currency_id.id
        
        kjc_obj = self.pool.get('kderp.job.currency')
        kebl_obj = self.pool.get('kderp.expense.budget.line')
        
        for id in ids:
            res[id]={'cost_vnd':0.0,
                     'cost_usd':0.0,
                     'paid_vnd':0.0,
                     'paid_usd':0.0}
            
        kebl_obj_ids = kebl_obj.search(cr, uid, [('account_analytic_id','in',ids)])
        #raise osv.except_osv("E",kebl_obj_ids)
        for kebl in kebl_obj.browse(cr, uid, kebl_obj_ids, context):
            res[kebl.account_analytic_id.id]['cost_vnd']+=kebl.amount
            res[kebl.account_analytic_id.id]['paid_vnd']+=kebl.payment_amount
            
            res[kebl.account_analytic_id.id]['cost_usd']+=kjc_obj.compute(cr, uid, company_currency_id, 'USD',kebl.account_analytic_id.id, kebl.amount)
            res[kebl.account_analytic_id.id]['paid_usd']+=kjc_obj.compute(cr, uid, company_currency_id, 'USD',kebl.account_analytic_id.id, kebl.payment_amount)
        return res
            
    def _get_job_contract_info(self, cr, uid, ids, name, arg, context=None):
        res = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_currency = user.company_id.currency_id
        company_currency_id = user.company_id.currency_id.id
        
        cur_obj = self.pool.get('res.currency')
        kcc_obj = self.pool.get('kderp.contract.currency')
        kqcpl_obj = self.pool.get('kderp.quotation.contract.project.line')
        
        #Duyet JOB
        for kp in self.browse(cr,uid,ids,context):
            Contracted_amount=0
            Contracted_amount_USD=0
            
            Claimed_amount=0
            Claimed_amount_USD=0
            
            Collected_Amount=0
            Collected_Amount_USD=0
            #Duyet Contract
            for kcc in kp.contract_ids:
                ctc_obj={}
                #Duyet Job Contract Currency, dua currency va amount vao ctc
                for kcpq_line in kcc.contract_job_summary_ids:
                    if kcpq_line.account_analytic_id.id==kp.id:
                        ctc_amount=(ctc_obj[kcpq_line.currency_id.id]['ctc_amount']+ kcpq_line.amount_currency) if kcpq_line.currency_id.id in ctc_obj else kcpq_line.amount_currency
                        ctc_obj[kcpq_line.currency_id.id]={'ctc_amount':ctc_amount,
                                                           'claimed_amount':0}
                #Duyet Payment          
                for kcp in kcc.client_payment_ids:
                    if kcp.state not in ('cancel','draft'):
                        exrate=kcp.exrate
                        for kpfc_line in kcp.invoice_line:
                            subtotal=kpfc_line.price_unit
                            if kpfc_line.account_analytic_id.id==kp.id:
                                if kcp.currency_id.id in ctc_obj:
                                    ctc_obj[kcp.currency_id.id]['claimed_amount']+=subtotal
                                elif company_currency_id in ctc_obj:#Neu Claim Currency ko co trong contract, quy doi sang company currency theo ti gia cua Contract
                                    ctc_obj[company_currency_id]['claimed_amount']+=kcc_obj.compute(cr, uid, kcp.currency_id.id,company_currency_id, kcc.id, subtotal)
                                    
                                Claimed_amount+=cur_obj.round(cr, uid, company_currency, exrate*subtotal) #Claimed Amount in Compnay Currency
                                
                                if kcp.currency_id.name=='USD':
                                    Claimed_amount_USD+=subtotal
                                else:
                                    Claimed_amount_USD+=kcc_obj.compute(cr, uid, kcp.currency_id.id, "USD", kcc.id, subtotal)
                                    
                                if kcp.state=='paid':
                                    if kcp.currency_id.name=='USD':
                                        Collected_Amount_USD+=subtotal
                                    else:
                                        Collected_Amount_USD+=kcc_obj.compute(cr, uid, kcp.currency_id.id, "USD", kcc.id, subtotal)
                                    Collected_Amount+=cur_obj.round(cr, uid, company_currency, exrate*subtotal)
                
                Contracted_amount=Claimed_amount
                Contracted_amount_USD+=Claimed_amount_USD
                
                for curr_id in ctc_obj:
                    contracted_remain=ctc_obj[curr_id]['ctc_amount']-ctc_obj[curr_id]['claimed_amount']
                    Contracted_amount+=kcc_obj.compute(cr, uid, curr_id, company_currency_id, kcc.id, contracted_remain)
                    Contracted_amount_USD+=kcc_obj.compute(cr, uid, curr_id, "USD", company_currency_id, kcc.id, contracted_remain) 
                
            res[kp.id]={"contracted_amount":Contracted_amount,
                        "contracted_amount_usd":Contracted_amount_USD,
                        "claimed_amount":Claimed_amount,
                        "claimed_amount_usd":Claimed_amount_USD,
                        "collected_amount":Collected_Amount,
                        "collected_amount_usd":Collected_Amount_USD}
        return res
    
    def _get_job_contract_from_contract_currency(self, cr, uid, ids, context=None):
        res=[]
        for kccur in self.browse(cr,uid,ids):
            for kcpq_line in kccur.contract_id.contract_job_summary_ids:
                res.append(kcpq_line.account_analytic_id.id)
        return res
    
    def _get_job_contract_from_contract_project_line(self, cr, uid, ids, context=None):
        res=[]
        for kcpl in self.browse(cr,uid,ids):
            res.append(kcpl.account_analytic_id.id)
        return res
    
    def _get_job_contract_from_client_payment(self, cr, uid, ids, context=None):
        res=[]
        for kcp in self.browse(cr,uid,ids):
            for kcpq_line in kcp.contract_id.contract_job_summary_ids:
                res.append(kcpq_line.account_analytic_id.id)
        return res
    
    def _get_job_contract_from_client_payment_line(self, cr, uid, ids, context=None):
        res=[]
        for kcpl in self.browse(cr,uid,ids):
            for kcpq_line in kcpl.invoice_id.contract_id.contract_job_summary_ids:
                res.append(kcpq_line.account_analytic_id.id)
        return res
    
    def _get_job_from_job_currency(self, cr, uid, ids, context=None):
        res=[]
        for kjc in self.browse(cr,uid,ids):
            res.append(kjc.account_analytic_id.id)
        return res
    
    def _get_job_from_job_budget_line(self, cr, uid, ids, context=None):
        res=[]
        for kebl in self.browse(cr,uid,ids):
            res.append(kebl.account_analytic_id.id)
        return res
    
    _columns={             
              #Contracted Info
               'contracted_amount':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Contracted Amount',multi='get_job_amount_summary_info',
                                                   store={
                                                          'kderp.contract.currency':(_get_job_contract_from_contract_currency,None,35),
                                                          'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                          'account.invoice':(_get_job_contract_from_client_payment,None,35),
                                                          'account.invoice.line':(_get_job_contract_from_client_payment_line,None,35),
                                                        }),
               'contracted_amount_usd':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Contracted Amount',multi='get_job_amount_summary_info',
                                                   store={
                                                          'kderp.contract.currency':(_get_job_contract_from_contract_currency,None,35),
                                                          'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                          'account.invoice':(_get_job_contract_from_client_payment,None,35),
                                                          'account.invoice.line':(_get_job_contract_from_client_payment_line,None,35),
                                                        }),
                
               'claimed_amount':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Claimed',multi='get_job_amount_summary_info',
                                                   store={
                                                          'kderp.contract.currency':(_get_job_contract_from_contract_currency,None,35),
                                                          'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                          'account.invoice':(_get_job_contract_from_client_payment,None,35),
                                                          'account.invoice.line':(_get_job_contract_from_client_payment_line,None,35),
                                                        }),
               'claimed_amount_usd':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Claimed USD',multi='get_job_amount_summary_info',
                                                   store={
                                                          'kderp.contract.currency':(_get_job_contract_from_contract_currency,None,35),
                                                          'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                          'account.invoice':(_get_job_contract_from_client_payment,None,35),
                                                          'account.invoice.line':(_get_job_contract_from_client_payment_line,None,35),
                                                        }),
               
               'collected_amount':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Collected',multi='get_job_amount_summary_info',
                                                   store={
                                                          'kderp.contract.currency':(_get_job_contract_from_contract_currency,None,35),
                                                          'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                          'account.invoice':(_get_job_contract_from_client_payment,None,35),
                                                          'account.invoice.line':(_get_job_contract_from_client_payment_line,None,35),
                                                        }),
               'collected_amount_usd':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Collected USD',multi='get_job_amount_summary_info',
                                                   store={
                                                          'kderp.contract.currency':(_get_job_contract_from_contract_currency,None,35),
                                                          'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                          'account.invoice':(_get_job_contract_from_client_payment,None,35),
                                                          'account.invoice.line':(_get_job_contract_from_client_payment_line,None,35),
                                                        }),
               
               'cost_vnd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Budget'),method=True,string='Cost VND',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),                                                 
                                                 }),
               'cost_usd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Cost USD',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),                                                 
                                                 }),
               'paid_vnd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Paid VND',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),                                                 
                                                 }),
               'paid_usd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Paid USD',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),                                                 
                                                 })
             }
    _defaults={
               'contracted_amount':lambda *a:0,
               'contracted_amount_usd':lambda *a:0,
               'claimed_amount':lambda *a:0,
               'claimed_amount_usd':lambda *a:0,
               'collected_amount':lambda *a:0,
               'collected_amount_usd':lambda *a:0
               }   
account_analytic_account()