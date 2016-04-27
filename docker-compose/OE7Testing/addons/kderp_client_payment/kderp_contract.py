from openerp.osv.orm import Model
from openerp.osv import fields
import openerp.addons.decimal_precision as dp
import re


class kderp_contract_client(Model):
    _name = 'kderp.contract.client'
    _inherit = 'kderp.contract.client'
    _description='KDERP Contract to Client'
    
    def _get_contract_summary_info(self, cr, uid, ids, name, arg, context=None):
        res = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_currency_id = user.company_id.currency_id.id
        kcc_obj = self.pool.get('kderp.contract.currency')
        from kderp_base.kderp_base import round_base
        
        for ctc in self.browse(cr,uid,ids):
            contract_obj={}
            #Them tong gia tri cua contract vao mot object, kiem tra xem currency co giong currency cua company khong 
            for ctc_curr in ctc.contract_summary_currency_ids:
                contract_obj.update({ctc_curr.name.id:{'amount':ctc_curr.amount,'tax_amount':ctc_curr.tax_amount,'currency_id':ctc_curr.name.id,
                                                       'must_convert':company_currency_id!=ctc_curr.name.id}})

            contracted_amount = 0.0
            contracted_tax = 0.0
            contracted_total = 0.0
            
            contract_claim_amount = 0.0
            contract_claim_tax = 0.0
            contract_claim_total = 0.0
            
            contract_collect_amount = 0.0
            contract_collect_tax = 0.0
            contract_collect_total = 0.0
            ##########Lap payment
            
            for inv in ctc.client_payment_ids:
                if inv.state not in ('cancel','draft') and inv.currency_id.id in contract_obj:
                    #Tru dan gia tri hop dong
                    #if inv.payment_term_id.type=='p':
                    #    amount = inv.amount
                    #elif inv.payment_term_id.type=='re':
                    #    amount = inv.retention
                    #else:
                    #    amount = inv.advanced
                    
                    amount = inv.amount_untaxed
                    tax_amount = inv.amount_tax
                    
                    cur_id = inv.currency_id.id 
                    
                    ctc_cal_id =cur_id
                    contract_obj[ctc_cal_id].update({'amount':contract_obj[ctc_cal_id]['amount']-amount,
                                                     'tax_amount':contract_obj[ctc_cal_id]['tax_amount']-tax_amount})
                    
                    #Tinh phan da claim
                    amount_untaxed = inv.amount_untaxed
                    amount_tax = inv.amount_tax
                    amount_total = inv.amount_total
                    
                    if company_currency_id!=inv.currency_id.id:
                        if inv.state in ('proforma2','proforma'):
                            amount_untaxed = kcc_obj.compute(cr, uid, cur_id, company_currency_id, inv.contract_id.id, amount_untaxed)
                            amount_tax = kcc_obj.compute(cr, uid, cur_id, company_currency_id, inv.contract_id.id, amount_tax)
                            amount_total = kcc_obj.compute(cr, uid, cur_id, company_currency_id, inv.contract_id.id, amount_total)
                        else:
                            amount_untaxed = inv.amount_untaxed*inv.exrate
                            amount_tax = inv.amount_tax*inv.exrate
                            amount_total = inv.amount_total*inv.exrate
                    
                    if inv.state!='paid':
                        contract_claim_amount+=amount_untaxed
                        contract_claim_tax+=amount_tax
                        contract_claim_total+=amount_total
                    
                    if inv.state=='paid':
                        collected_total_amount_vnd=0
                        for kr in inv.received_ids:
                            collected_total_amount_vnd+=kr.amount*kr.exrate                        
                        #Calculation base on Collected Amount
                        #claim_tax= round_base((amount_tax / amount_untaxed if amount_untaxed<>0 else 0)*100,5)                        
                        
                        #Collected                        
                        collected_vnd_subtotal = round_base(inv.amount_untaxed * inv.exrate, 5)  #collected_total_amount_vnd/(1+claim_tax/100.0)
                        collected_vnd_tax = round_base(inv.amount_tax * inv.exrate, 5) # collected_vnd_subtotal*claim_tax/100.0

                        contract_collect_total+=collected_total_amount_vnd
                        contract_collect_amount+=collected_vnd_subtotal
                        contract_collect_tax+=collected_vnd_tax
                        
                        #Claimed
                        contract_claim_amount+=collected_vnd_subtotal
                        contract_claim_tax+=collected_vnd_tax
                        contract_claim_total+=collected_total_amount_vnd
                        
            ##########Ket thuc Lap payment
            for sctc in contract_obj:
                if not contract_obj[sctc]['must_convert']:
                    contracted_amount+=contract_obj[sctc]['amount']
                    contracted_tax+=contract_obj[sctc]['tax_amount']
                else:
                    contracted_amount+=kcc_obj.compute(cr, uid, contract_obj[sctc]['currency_id'], company_currency_id, ctc.id, contract_obj[sctc]['amount'])
                    contracted_tax+=kcc_obj.compute(cr, uid, contract_obj[sctc]['currency_id'], company_currency_id, ctc.id, contract_obj[sctc]['tax_amount'])

            contracted_amount+=contract_claim_amount
            contracted_tax+=contract_claim_tax
            contracted_total=contracted_amount+contracted_tax
            
            res[ctc.id] = { 'contracted_amount':contracted_amount,
                            'contracted_tax':contracted_tax,
                            'contracted_total':contracted_total,
                            
                            'contract_claim_amount':contract_claim_amount,
                            'contract_claim_tax':contract_claim_tax,
                            'contract_claim_total':contract_claim_total,
                            
                            'contract_collect_amount':contract_collect_amount,
                            'contract_collect_tax':contract_collect_tax,
                            'contract_collect_total':contract_collect_total,
                            
                            'contract_receivable_amount':contract_claim_amount-contract_collect_amount,
                            'contract_receivable_tax':contract_claim_tax-contract_collect_tax,
                            'contract_receivable_total':contract_claim_total-contract_collect_total,
                            
                            'balance_amount':contracted_amount - contract_collect_amount,
                            'balance_tax':contracted_tax - contract_collect_tax,
                            'balance_total':contracted_total -contract_collect_total
                            }
        return res
    
    def _get_contract(self, cr, uid, ids, context=None):
        res={}
        for inv in self.browse(cr,uid,ids):
            res[inv.contract_id.id] = True
        return res.keys()
    
    def _get_contract_from_ccurrency(self, cr, uid, ids, context=None):
        res={}
        for ctc in self.browse(cr,uid,ids):
            res[ctc.contract_id.id] = True
        return res.keys()
    
    def _get_job_contract_from_contract_project_line(self, cr, uid, ids, context=None):
        res=[]
        for kcpl in self.pool.get('kderp.quotation.contract.project.line').browse(cr,uid,ids):
            res.append(kcpl.contract_id.id)
        return list(set(res))
    
    _columns={
              'client_payment_ids':fields.one2many('account.invoice','contract_id','Payments',readonly=1),
              'contract_summary_currency_info_ids':fields.one2many('kderp.contract.currency','contract_id',domain=[('default_curr','=',True)],readonly=True),
              
              #Contracted Info
              'contracted_amount':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Contracted Amount',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              
              'contracted_tax':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Contracted VAT',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              'contracted_total':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Contracted Total',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
             
              #Claim Info
              'contract_claim_amount':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Claim Amount',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),           
              'contract_claim_tax':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Claim VAT',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              'contract_claim_total':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Claim Total',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),              
              #Collect Info
              'contract_collect_amount':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Collect Amount',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),              
              'contract_collect_tax':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Collect VAT',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              'contract_collect_total':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Collect Total',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              
              #Receivable Info
              'contract_receivable_amount':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Receivable Amount',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),              
              'contract_receivable_tax':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Receivable VAT',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              'contract_receivable_total':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Receivable Total',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              
              #Balance Info
              'balance_amount':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Balance Amount',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),              
              'balance_tax':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Balance VAT',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              'balance_total':fields.function(_get_contract_summary_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Balance Total',multi='get_contract_info',
                                             store={
                                                    'kderp.contract.client':(lambda self, cr, uid, ids, c={}: ids, ['contract_currency_ids','contract_summary_currency_ids'],25),
                                                    'account.invoice':(_get_contract,['state','invoice_line','currency_id','journal_id','contract_id'],25),
                                                    'kderp.quotation.contract.project.line':(_get_job_contract_from_contract_project_line,None,35),
                                                    'kderp.contract.currency':(_get_contract_from_ccurrency, None, 25)}),
              }

    _defaults={
               'contracted_amount':lambda *a:0,
               'contracted_tax':lambda *a:0,
               'contracted_total':lambda *a:0,
               
               'contract_claim_amount':lambda *a:0,
               'contract_claim_tax':lambda *a:0,
               'contract_claim_total':lambda *a:0,
               
               'contract_collect_amount':lambda *a:0,
               'contract_collect_tax':lambda *a:0,
               'contract_collect_total':lambda *a:0,
               }
    
   
kderp_contract_client()
