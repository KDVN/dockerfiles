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
            
        job_ids=",".join(map(str,ids))
        # = kebl_obj.search(cr, uid, [('account_analytic_id','in',ids)])

        cr.execute("""Select 
                            kebl.account_analytic_id,
                            sum(coalesce(amount,0)) as amount,
                            sum(coalesce(payment_amount,0)) as payment_amount,
                            case when 
                                coalesce(kjc.rate,0)=0 then 0
                            else
                                round(sum(coalesce(amount,0))/kjc.rate/kjc.rounding,0)*kjc.rounding end as cost_usd,
                            case when 
                                coalesce(kjc.rate,0)=0 then 0
                            else
                                round(sum(coalesce(payment_amount,0))/kjc.rate/kjc.rounding,0)*kjc.rounding end as payment_usd
                        from 
                            kderp_expense_budget_line kebl
                        left join
                            kderp_job_currency kjc on kebl.account_analytic_id=kjc.account_analytic_id 
                        inner join
                            res_currency rc on kjc.name=rc.id and rc.name='USD'
                        where
                            kebl.account_analytic_id in (%s)
                        group by
                            kebl.account_analytic_id,
                            kjc.id""" % (job_ids))
        #raise osv.except_osv("E",cr.fetchall())
        for job_id,amount,payment_amount,cost_usd,payment_usd in cr.fetchall():
            res[job_id]['cost_vnd']+=amount
            res[job_id]['paid_vnd']+=payment_amount
            
            res[job_id]['cost_usd']+=cost_usd#kjc_obj.compute(cr, uid, company_currency_id, 'USD',job_id,amount)
            res[job_id]['paid_usd']+=payment_usd#kjc_obj.compute(cr, uid, company_currency_id, 'USD',job_id,payment_amount)
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
                if kcc.availability == 'inused':
                    #Duyet Job Contract Currency, dua currency va amount vao ctc
                    for kcpq_line in kcc.contract_job_summary_ids:
                        if kcpq_line.account_analytic_id.id==kp.id:
                            ctc_amount=(ctc_obj[kcpq_line.currency_id.id]['ctc_amount'] + kcpq_line.amount_currency) if kcpq_line.currency_id.id in ctc_obj else kcpq_line.amount_currency
                            ctc_obj[kcpq_line.currency_id.id]={'ctc_amount':ctc_amount,
                                                               'claimed_amount':0}                    
                    #Duyet Payment
                    Claimed_amount_CTC_USD=0
                    Claimed_amount_CTC=0          
                    for kcp in kcc.client_payment_ids:
                        if kcp.state not in ('cancel','draft'):
                            exrate=kcp.exrate
                            for kpfc_line in kcp.invoice_line:
                                subtotal=kpfc_line.price_unit
                                if kpfc_line.account_analytic_id.id==kp.id:
                                    if kcp.currency_id.id in ctc_obj:
                                        ctc_obj[kcp.currency_id.id]['claimed_amount']+=subtotal
                                    elif company_currency_id in ctc_obj:#Neu Claim Currency ko co trong contract, quy doi sang company currency theo ti gia cua Contract
                                        ctc_obj[company_currency_id]['claimed_amount']+=kcc_obj.compute(cr, uid, kcp.currency_id.id, company_currency_id, kcc.id, subtotal)
                                        
                                    Claimed_amount_CTC+=cur_obj.round(cr, uid, company_currency, exrate*subtotal) #Claimed Amount in Company Currency
                                    
                                    if kcp.currency_id.name=='USD':
                                        Claimed_amount_CTC_USD+=subtotal
                                    else:
                                        Claimed_amount_CTC_USD+=kcc_obj.compute(cr, uid, kcp.currency_id.id, "USD", kcc.id, subtotal)
                                        
                                    if kcp.state=='paid':
                                        if kcp.currency_id.name=='USD':
                                            Collected_Amount_USD+=subtotal
                                        else:
                                            Collected_Amount_USD+=kcc_obj.compute(cr, uid, kcp.currency_id.id, "USD", kcc.id, subtotal)
                                        Collected_Amount+=cur_obj.round(cr, uid, company_currency, exrate*subtotal)
                    Claimed_amount+=Claimed_amount_CTC
                    Claimed_amount_USD+=Claimed_amount_CTC_USD
                    Contracted_amount+=Claimed_amount_CTC
                    Contracted_amount_USD+=Claimed_amount_CTC_USD
                    
                    for curr_id in ctc_obj:
                        contracted_remain = ctc_obj[curr_id]['ctc_amount']-ctc_obj[curr_id]['claimed_amount']
                        Contracted_amount += kcc_obj.compute(cr, uid, curr_id, company_currency_id, kcc.id, contracted_remain) if abs(contracted_remain) >=1 else 0
                        Contracted_amount_USD += kcc_obj.compute(cr, uid, curr_id, "USD", kcc.id, contracted_remain) 
    #            raise osv.except_osv("E",ctc_obj)
            res[kp.id]={"contracted_amount":Contracted_amount,
                        "contracted_amount_usd":Contracted_amount_USD,
                        "claimed_amount":Claimed_amount,
                        "claimed_amount_usd":Claimed_amount_USD,
                        "collected_amount":Collected_Amount,
                        "collected_amount_usd":Collected_Amount_USD}            
        return res
    
    def _get_job_contract_from_contract_currency(self, cr, uid, ids, context=None):
        res=[]
        for kccur in self.pool.get('kderp.contract.currency').browse(cr,uid,ids):
            for kcpq_line in kccur.contract_id.contract_job_summary_ids:
                res.append(kcpq_line.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_contract_from_contract_project_line(self, cr, uid, ids, context=None):
        res=[]
        for kcpl in self.pool.get('kderp.quotation.contract.project.line').browse(cr,uid,ids):
            res.append(kcpl.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_contract_from_client_payment(self, cr, uid, ids, context=None):
        res=[]
        for kcp in self.pool.get('account.invoice').browse(cr,uid,ids):
            for ail in kcp.invoice_line:
                res.append(ail.account_analytic_id.id)
            for kcpq_line in kcp.contract_id.contract_job_summary_ids:
                res.append(kcpq_line.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_contract_from_client_payment_line(self, cr, uid, ids, context=None):
        res=[]
        for kcpl in self.pool.get('account.invoice.line').browse(cr,uid,ids):
            res.append(kcpl.account_analytic_id.id)
            for kcpq_line in kcpl.invoice_id.contract_id.contract_job_summary_ids:
                res.append(kcpq_line.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_from_job_currency(self, cr, uid, ids, context=None):
        res=[]
        for kjc in self.pool.get('kderp.job.currency').browse(cr,uid,ids):
            res.append(kjc.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_from_job_expense_budget_line(self, cr, uid, ids, context=None):
        res=[]
        for kebl in self.pool.get("kderp.expense.budget.line").browse(cr,uid,ids):
            res.append(kebl.account_analytic_id.id)
        
        return list(set(res))
    
#JOB ISSUED
    def _get_job_issued_info(self, cr, uid, ids, name, arg, context=None):
        res={}
        job_ids=",".join(map(str,ids))
        for id in ids:
            cr.execute("""Select 
                                aaa.id as job_id,
                                sum(coalesce(vwpayment_vat.issued_vat,0)*
                                            case when coalesce((select sum(coalesce(amount,0)) from vwaccount_invoice_line ail where invoice_id=ai.id),0)=0 then 0 else coalesce(ail.amount,0)/coalesce((select sum(coalesce(amount,0)) from vwaccount_invoice_line ail where invoice_id=ai.id),0) end) as vat_issued_amount,
                                
                                sum(coalesce(issued_subtotal,0)*
                                            case when coalesce((select sum(coalesce(amount,0)) from vwaccount_invoice_line ail where invoice_id=ai.id),0)=0 then 0 else coalesce(ail.amount,0)/coalesce((select sum(coalesce(amount,0)) from vwaccount_invoice_line ail where invoice_id=ai.id),0) end) as vat_issued_subtotal
                            from
                                account_analytic_account aaa
                            left join 
                                 vwaccount_invoice_line ail on aaa.id=ail.account_analytic_id
                            left join
                                 account_invoice ai on invoice_id=ai.id
                            left join
                                (Select
                                    payment_id,
                                    sum(kpvi.amount/(1+coalesce(tax_percent,0)/100)) as issued_subtotal,
                                    sum(case when coalesce(tax_percent,0)=0 then 0 else  kpvi.amount/(1+coalesce(tax_percent,0)/100)/tax_percent end) as issued_vat
                                from 
                                    kderp_payment_vat_invoice kpvi 
                                left join
                                    kderp_invoice ki on vat_invoice_id=ki.id
                                where
                                    payment_id in (Select distinct invoice_id from account_invoice_line where coalesce(account_analytic_id,0) in (%s))
                                group by
                                    payment_id) vwpayment_vat on ai.id=vwpayment_vat.payment_id and coalesce(vwpayment_vat.payment_id,0)>0
                            where
                                ai.state!='cancel' and coalesce(aaa.id,0) in (%s)
                            group by
                                aaa.id""" % (job_ids,job_ids))
        for job_list in cr.dictfetchall():
            job_id=job_list.pop('job_id')
            res[job_id]=job_list
        return res                
                
    def _get_job_issued_from_from_client_payment(self, cr, uid, ids, context=None):
        res=[]
        for kcp in self.pool.get('account.invoice').browse(cr,uid,ids):
            for kcp_line in kcp.invoice_line:
                res.append(kcp_line.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_issued_from_client_payment_line(self, cr, uid, ids, context=None):
        res=[]
        for kcp_line in self.pool.get('account.invoice.line').browse(cr,uid,ids):
            res.append(kcp_line.account_analytic_id.id)
        return list(set(res))
    
    def __get_job_issued_from_vat_allocated(self, cr, uid, ids, context=None):
        res=[]
        for kpvi in self.pool.get('kderp.payment.vat.invoice').browse(cr,uid,ids):
            if kpvi.payment_id:
                for kcp_line in kpvi.payment_id.invoice_line: 
                    res.append(kcp_line.account_analytic_id.id)
        return list(set(res))
    
    def __get_job_issued_from_vat_invoice(self, cr, uid, ids, context=None):
        res=[]
        if ids:
            vat_ids=','.join(map(str,ids))
            cr.execute("""Select 
                            distinct account_analytic_id 
                        from 
                            kderp_payment_vat_invoice kpvi
                        left join
                            account_invoice_line ail on payment_id = invoice_id
                        where
                            coalesce(vat_invoice_id,0) in (%s)""" % (vat_ids))
            for job_id in cr.fetchall():
                res.append(job_id[0])
        return list(set(res))
    
#JOB RECEIVED VAT    
    def _get_job_received_from_supplier_payment(self, cr, uid, ids, context=None):
        res=[]
        for ksp in self.pool.get('kderp.supplier.payment').browse(cr,uid,ids):
            for kspl in ksp.payment_line:
                res.append(kspl.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_received_from_supplier_payment_line(self, cr, uid, ids, context=None):
        res=[]
        for kspl in self.pool.get('kderp.supplier.payment.line').browse(cr,uid,ids):
            res.append(kspl.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_received_from_supplier_payment_expense(self, cr, uid, ids, context=None):
        res=[]
        for kspe in self.pool.get('kderp.supplier.payment.expense').browse(cr,uid,ids):
            for kspel in kspe.payment_line:
                res.append(kspel.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_received_from_supplier_payment_expense_line(self, cr, uid, ids, context=None):
        res=[]
        for kspel in self.pool.get('kderp.supplier.payment.expense.line').browse(cr,uid,ids):
            res.append(kspel.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_received_from_supplier_vat(self, cr, uid, ids, context=None):
        res=[]
        for kpvi in self.pool.get('kderp.supplier.vat.invoice').browse(cr,uid,ids):
            for ksp in kpvi.kderp_supplier_payment_ids:
                for kspl in ksp.payment_line:
                    res.append(kspl.account_analytic_id.id)
                    
            for kspe in kpvi.kderp_supplier_payment_expense_ids:
                for kspel in kspe.payment_line:
                    res.append(kspel.account_analytic_id.id)
        return list(set(res))
    
    def _get_job_received_info(self, cr, uid, ids, name, arg, context=None):
        res={}
        job_ids=",".join(map(str,ids))
        #Tinh base on tren % cua Job o PO

        cr.execute("""Select 
                        vwtemp_job_per.account_analytic_id,
                        sum(job_per*vat_amount*po_final_exrate * case when coalesce(po_id,0)=0 then 1 else rate end) as vat_received_amount,
                        sum(job_per*subtotal_vat_amount*po_final_exrate * case when coalesce(po_id,0)=0 then 1 else rate end) as vat_received_subtotal
                    from
                        purchase_order po
                    left join
                        product_pricelist pp on pricelist_id = pp.id
                    left join
                        (Select 
                            po.id as po_id,
                            max(rcr.name) as max_date
                        from 
                            purchase_order po
                        left join
                            product_pricelist pp on po.pricelist_id = pp.id
                        left join
                            res_currency_rate rcr on pp.currency_id=rcr.currency_id and po.date_order>=rcr.name
                        where
                            pp.currency_id<>(Select currency_id from res_company rc limit 1)
                            and po.id in (Select distinct order_id from purchase_order_line where account_analytic_id in (%s)) --DK1
                        group by
                            po.id) vwpo_rate on po.id = po_id
                    left join
                        res_currency_rate rcr on max_date = rcr.name and pp.currency_id = rcr.currency_id
                    left join
                        (Select 
                            pol.order_id,
                            pol.account_analytic_id,
                            case when 
                            coalesce(grant_total,0)=0 then 0
                            else
                            sum(coalesce(final_subtotal,0))/grant_total end as job_per
                        from 
                            purchase_order_line pol
                        left join
                            purchase_order po on order_id = po.id
                        left join
                            (Select
                            order_id,
                            sum(coalesce(final_subtotal,0)) as grant_total
                            from 
                            purchase_order_line pol
                            where
                            order_id in (Select distinct order_id from purchase_order_line where account_analytic_id in (%s)) --DK2
                            group by
                            order_id) vwgrant_total on pol.order_id=vwgrant_total.order_id
                        where
                            pol.order_id in (Select distinct order_id from purchase_order_line where account_analytic_id in (%s)) and --DK3 
                            po.state not in ('draft','cancel')
                        group by
                            pol.order_id,
                            pol.account_analytic_id,
                            grant_total) vwtemp_job_per on po.id = order_id            
                    where                        
                        vwtemp_job_per.account_analytic_id in (%s) --Dk4
                    Group by
                        vwtemp_job_per.account_analytic_id""" % (job_ids,
                                                                 job_ids,
                                                                 job_ids,
                                                                 job_ids))
        #raise osv.except_osv("E",cr.fetchall())
        for id in ids:
            res[id]={'vat_received_amount':0,
                     'vat_received_subtotal':0}
      
        for job_id,vat_amount,vat_subtotal in cr.fetchall():
            res[job_id]['vat_received_amount']=vat_amount or 0
            res[job_id]['vat_received_subtotal']=vat_subtotal or 0
            
        #Job VAT Received Other Expense
        cr.execute("""Select 
                        vwtemp_job_per.account_analytic_id,
                        sum(job_per * vat_amount *  case when coalesce(exp_id,0)=0 then 1 else rate end) as vat_received_amount,
                        sum(job_per * subtotal_vat_amount * case when coalesce(exp_id,0)=0 then 1 else rate end) as vat_received_subtotal
                    from
                        kderp_other_expense koe
                    left join
                        (Select 
                            koe.id as exp_id,
                            max(rcr.name) as max_date
                        from 
                            kderp_other_expense koe
                        left join
                            res_currency_rate rcr on koe.currency_id=rcr.currency_id and koe.date>=rcr.name
                        where
                            koe.currency_id<>(Select currency_id from res_company rc limit 1)
                            and 
                            koe.id in (Select distinct expense_id from kderp_other_expense_line where account_analytic_id in (%s)) --Dk1
                        group by
                            koe.id) vwexp_rate on koe.id = exp_id
                    left join
                        res_currency_rate rcr on max_date = rcr.name and koe.currency_id = rcr.currency_id    
                    left join
                        (Select 
                            koel.expense_id,
                            koel.account_analytic_id,
                            case when 
                            coalesce(grant_total,0)=0 then 0
                            else
                            sum(coalesce(amount,0))/grant_total end as job_per
                        from 
                            kderp_other_expense_line koel
                        left join
                            kderp_other_expense koe on expense_id = koe.id
                        left join
                            (Select
                            expense_id,
                            sum(coalesce(amount,0)) as grant_total
                            from 
                            kderp_other_expense_line koel
                            where
                            expense_id in (Select distinct expense_id from kderp_other_expense_line where account_analytic_id in (%s)) --DK2
                            group by
                            expense_id) vwgrant_total on koel.expense_id = vwgrant_total.expense_id
                        where
                            koel.expense_id in (Select distinct expense_id from kderp_other_expense_line where account_analytic_id in (%s)) and  --DK3
                            koe.state not in ('draft','cancel')
                        group by
                            koel.expense_id,
                            koel.account_analytic_id,
                            grant_total) vwtemp_job_per on koe.id = expense_id
                    where                        
                        vwtemp_job_per.account_analytic_id in (%s) --DK4
                    Group by
                        vwtemp_job_per.account_analytic_id;""" % (job_ids,
                                                                  job_ids,
                                                                  job_ids,
                                                                  job_ids))
        for job_id,vat_amount,vat_subtotal in cr.fetchall():
            res[job_id]['vat_received_amount']+=vat_amount or 0
            res[job_id]['vat_received_subtotal']+=vat_subtotal or 0
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
               'contracted_amount_usd':fields.function(_get_job_contract_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Contracted Amount USD',multi='get_job_amount_summary_info',
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
               
               'need_update':fields.boolean('Need Update Summary Amount'),
               
               'cost_vnd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Budget'),method=True,string='Cost VND',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_expense_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),
                                                 'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['need_update'], 50),                                                 
                                                 }),
               'cost_usd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Cost USD',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_expense_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),
                                                 'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['need_update'], 50),                                                 
                                                 }),
               'paid_vnd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Paid VND',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_expense_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),
                                                 'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['need_update'], 50),                                                 
                                                 }),
               'paid_usd':fields.function(_get_job_cost_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Paid USD',multi='get_job_cost_amount_summary_info',
                                          store={
                                                 'kderp.expense.budget.line':(_get_job_from_job_expense_budget_line,None,50),
                                                 'kderp.job.currency':(_get_job_from_job_currency,None,50),
                                                 'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['need_update'], 50),                    
                                                 }),
              
               'vat_issued_amount':fields.function(_get_job_issued_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='VAT Issued',multi='_get_issued_vat',
                                                 store={
                                                        'account.invoice':(_get_job_issued_from_from_client_payment,None,35),
                                                        'account.invoice.line':(_get_job_issued_from_client_payment_line,None,35),
                                                        'kderp.payment.vat.invoice':(__get_job_issued_from_vat_allocated,None,35),
                                                        'kderp.invoice':(__get_job_issued_from_vat_invoice,None,35),
                                                      }),
              
               'vat_issued_subtotal':fields.function(_get_job_issued_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='Issued Amount',multi='_get_issued_vat',
                                                 store={
                                                        'account.invoice':(_get_job_issued_from_from_client_payment,None,35),
                                                        'account.invoice.line':(_get_job_issued_from_client_payment_line,None,35),
                                                        'kderp.payment.vat.invoice':(__get_job_issued_from_vat_allocated,None,35),
                                                        'kderp.invoice':(__get_job_issued_from_vat_invoice,None,35),
                                                      }),
              
              'vat_received_amount':fields.function(_get_job_received_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='VAT Received',multi='_get_received_vat',
                                                 store={
                                                        'kderp.supplier.payment':(_get_job_received_from_supplier_payment,['state','tax_base','taxes_id','currency_id','order_id','state','amount','advanced_amount','retention_amount'],35),
                                                        'kderp.supplier.payment.line':(_get_job_received_from_supplier_payment_line,None,35),
                                                        'kderp.supplier.payment.expense':(_get_job_received_from_supplier_payment_expense,['state','currency_id','taxes_id'],35),
                                                        'kderp.supplier.payment.expense.line':(_get_job_received_from_supplier_payment_expense_line,None,35),
                                                        'kderp.supplier.vat.invoice':(_get_job_received_from_supplier_vat,None,35),
                                                        'kderp.expense.budget.line':(_get_job_from_job_expense_budget_line,None,50),
                                                        'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['need_update'], 50),
                                                      }),
              
               'vat_received_subtotal':fields.function(_get_job_received_info,type='float',digits_compute=dp.get_precision('Budget'), method=True,string='VAT Subtotal',multi='_get_received_vat',
                                                 store={
                                                        'kderp.supplier.payment':(_get_job_received_from_supplier_payment,['state','tax_base','taxes_id','currency_id','order_id','state','amount','advanced_amount','retention_amount'],35),
                                                        'kderp.supplier.payment.line':(_get_job_received_from_supplier_payment_line,None,35),
                                                        'kderp.supplier.payment.expense':(_get_job_received_from_supplier_payment_expense,['state','currency_id','taxes_id'],35),
                                                        'kderp.supplier.payment.expense.line':(_get_job_received_from_supplier_payment_expense_line,None,35),
                                                        'kderp.supplier.vat.invoice':(_get_job_received_from_supplier_vat,None,35),
                                                        'kderp.expense.budget.line':(_get_job_from_job_expense_budget_line,None,50),
                                                        'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['need_update'], 50),
                                                      }),
             }
    _defaults={
               'contracted_amount':lambda *a:0,
               'contracted_amount_usd':lambda *a:0,
               'claimed_amount':lambda *a:0,
               'claimed_amount_usd':lambda *a:0,
               'collected_amount':lambda *a:0,
               'collected_amount_usd':lambda *a:0
               }
    
    def init(self,cr):
        cr.execute("""Create or replace view vwaccount_invoice_line as
                        Select 
                            account_analytic_id,
                            invoice_id,TAX_BASE,
                            case when tax_base='p' then ail.amount
                            else case when tax_base='p_adv' then ail.advanced
                            else case when tax_base='p_retention' then ail.retention
                            else ail.price_subtotal end end end as amount
                        from
                            account_invoice_line ail 
                        left join
                            account_invoice ai on invoice_id=ai.id;""")   
account_analytic_account()