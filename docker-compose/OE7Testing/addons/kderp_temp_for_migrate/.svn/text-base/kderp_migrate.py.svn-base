import time

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.osv.orm import browse_record, browse_null
from openerp.tools.translate import _

class kderp_migrate(osv.osv_memory):
    _name = "kderp.migrate"
    _description = "KDERP Migrate"
    
    def write_code_for_job_currency(self, cr, uid, ids, context):
        cr.execute("""UPDATE account_analytic_account set state_bar =state;""")
        cr.commit()
        cr.execute("Select id,code from account_analytic_account")
        aaa_job = self.pool.get('account.analytic.account')
        for id,code in cr.fetchall():
            result=aaa_job.write(cr, uid, [id],{'code':code})
        company_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        result = self.pool.get('res.company').write(cr, uid, [1], {'currency_id':company_currency_id})
        cr.execute("""Update account_analytic_account aaa set job_currency=kjc.name from kderp_job_currency kjc where default_curr =True and aaa.id = kjc.account_analytic_id """)
        return True
    
    def write_code_for_contract_currency(self, cr, uid, ids, context):
        cr.execute("Select id,code from kderp_contract_client")
        kcc_job = self.pool.get('kderp.contract.client')
        for id,code in cr.fetchall():
            result=kcc_job.write(cr, uid, [id],{'code':code})
        company_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        result = self.pool.get('res.company').write(cr, uid, [1], {'currency_id':company_currency_id})
        return True
    
    def write_contract_curr_dont_have_payment(self, cr ,uid , ids, context):
        cr.execute("""Select 
                        id,default_curr 
                    from 
                        kderp_contract_currency 
                    where 
                        contract_id not in (Select contract_id from account_invoice)""")
        kcc_job = self.pool.get('kderp.contract.currency')
        
        for cid,df in cr.fetchall():
            re=kcc_job.write(cr, uid, [cid], {'default_curr':df})
            cr.commit()
        return True
    
    def write_contract_curr_dont_have_amount(self, cr ,uid , ids, context):
        cr.execute("""Select 
                        id,
                        default_curr 
                    from 
                        kderp_contract_currency 
                    where 
                        contract_id in (select id from kderp_contract_client where coalesce(contracted_amount,0)=0)""")
        kcc_job = self.pool.get('kderp.contract.currency')
        
        for cid,df in cr.fetchall():
            re=kcc_job.write(cr, uid, [cid], {'default_curr':df})
            cr.commit()
        return True
    
    def write_contract_curr_dont_have_tax_amount(self, cr ,uid , ids, context):
        cr.execute("""Select 
                        id,
                        default_curr 
                    from 
                        kderp_contract_currency 
                    where 
                        contract_id in (select id from kderp_contract_client where coalesce(contracted_tax,0)=0 and coalesce(contract_claim_tax,0)>0)""")
        kcc_job = self.pool.get('kderp.contract.currency')
        
        for cid,df in cr.fetchall():
            re=kcc_job.write(cr, uid, [cid], {'default_curr':df})
            cr.commit()
        return True
    
    def write_job_error_amount_double(self, cr ,uid , ids, context):
        cr.execute("""Select id,currency_id from kderp_quotation_contract_project_line""")
        kqcpl_obj = self.pool.get('kderp.quotation.contract.project.line')
        
        for kqcpl_id,curr_id in cr.fetchall():
            re=kqcpl_obj.write(cr, uid, [kqcpl_id], {'currency_id':curr_id})
            cr.commit()
        return True

        
    def write_planned(self, cr, uid, ids, context):
        cr.execute("""Select 
                            max_id as id,
                            planned_amount
                        from
                            kderp_budget_data kbd
                        inner join
                            (Select
                                max(id) as max_id
                            from
                                kderp_budget_data
                            group by
                                account_analytic_id) vwgroup on kbd.id=max_id""")
        kbd_obj = self.pool.get('kderp.budget.data')
        for id,pl_amount in cr.fetchall():
            result=kbd_obj.write(cr, uid, [id],{'planned_amount':pl_amount})
        return True
    
    def write_budget_data(self, cr, uid, ids, context):

        kbd_obj = self.pool.get('kderp.budget.data')
        kbd_ids=kbd_obj.search(cr, uid,[('id','!=',0)])
        result=kbd_obj.write(cr, uid, kbd_ids,{})
        return True
    
    def write_budget_data_error_paid(self, cr, uid, ids, context):
        cr.execute("""Select id from kderp_budget_data  where coalesce(paid_amount,0)>coalesce(expense_amount,0)""")
        kbd_obj = self.pool.get('kderp.budget.data')
        for id in cr.fetchall():
            result=kbd_obj.write(cr, uid, [id[0]],{})
        return True
    
    def write_quotation_submit_line(self, cr, uid, ids, context):
        cr.execute("""Select 
                            id,
                            currency_id
                        from
                            kderp_sale_order_submit_line""")
        qs_obj = self.pool.get('kderp.sale.order.submit.line')
        fo=open("/home/openerp/soqsl_error.txt",'w')
        fo.write("")
        fo.close()
        fo=open("/home/openerp/soqsl_error.txt",'a')
        for id,curr_id in cr.fetchall():
            try:
                result=qs_obj.write(cr, uid, [id],{'currency_id':curr_id})
                cr.commit()
            except:
                fo.write(str(id))
                continue
        fo.close()                
        return True
    
    def write_so_contract_id(self, cr, uid, ids, context):
        cr.execute("""Select 
                            id,
                            contract_id 
                        from sale_order 
                        where 
                            coalesce(contract_id,0)>0 and 
                            coalesce(contract_id,0) not in (Select contract_id from kderp_quotation_contract_project_line ) and state not in ('draft','cancel');""")
        so_obj = self.pool.get('sale.order')
        fo=open("/home/openerp/so_error.txt",'w')
        fo.write("")
        fo.close()
        fo=open("/home/openerp/so_error.txt",'a')
        for id,contract_id in cr.fetchall():
            try:
                result=so_obj.write(cr, uid, [id],{'contract_id':contract_id})
                cr.commit()
            except:
                fo.write(str(id))
                cr.rollback()
                continue
        fo.close();
        return True
    
    def write_quotation(self, cr, uid, ids, context):
        cr.execute("""update sale_order set sort_state=case when state='done' then 1 else case when state='draft' then 2 else 3 end end """)
        cr.execute("""Select 
                            id,
                            state
                        from
                            sale_order so
                        where
                            so.state not in ('draft','cancel');
                            """)
        so_obj = self.pool.get('sale.order')
        fo=open("/home/openerp/so_error.txt",'w')
        fo.write("")
        fo.close()
        fo=open("/home/openerp/so_error.txt",'a')
        for id,state in cr.fetchall():
            try:
                result=so_obj.write(cr, uid, [id],{'state':'draft'})
                result=so_obj.write(cr, uid, [id],{'state':state})
                cr.commit()
            except:
                fo.write(str(id))
                continue
        fo.close();
        return True
    
    def write_sol(self, cr, uid, ids, context):
        cr.execute("""Select 
                            id,
                            discount
                        from
                            sale_order_line sol""")
        sol_obj = self.pool.get('sale.order.line')
        fo=open("/home/openerp/sol_error.txt",'w')
        fo.write("")
        fo.close()
        fo=open("/home/openerp/sol_error.txt",'a')
        for id,dc in cr.fetchall():
            try:
                result=sol_obj.write(cr, uid, [id],{'discount':dc})
                cr.commit()
            except:
                fo.write(str(id))
                continue
        fo.close();
        return True
    
    def update_client_payment_error_tax(self, cr, uid, ids, context):
        cr.execute("""Select 
                            ai.id,tax_base
                        from
                            account_invoice ai
                        where
                            coalesce(ai.number,'')='' and state='draft'""")
        ai_obj = self.pool.get('account.invoice')
        for inv_id,tb in cr.fetchall():
            ai_obj.write(cr,uid,inv_id,{'tax_base':tb})
        return True
    
    def update_client_payment_error_curr(self, cr, uid, ids, context):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                            ai.id,curr_state
                        from
                            account_invoice ai
                        left join
                            res_currency rc on currency_id=rc.id
                        where
                            rc.name<>'VND' and state='paid'""")
        ai_obj = self.pool.get('account.invoice')
        kr_obj = self.pool.get('kderp.received')
        ai_ids=[]
        loop=0
        fo=open("/home/openerp/processed_clp.txt",'w')
        fo.write(" ")
        fo.close()

        fo1=open("/home/openerp/processed_clp_error.txt",'w')
        fo1.write("")
        fo1.close()
        ai_ids=[]
        for inv_id,state in cr.fetchall():
            ai_ids.append(inv_id)
        
        for invoice in ai_obj.browse(cr, uid, ai_ids):
            if invoice.state=='paid':
                kr_ids=[]
                for kr in invoice.received_ids:
                    kr_obj.action_unreconcile(cr, uid, [kr.id])

        cr.execute("""Select 
                            ai.id,curr_state
                        from
                            account_invoice ai
                        left join
                            res_currency rc on currency_id=rc.id
                        where
                            rc.name<>'VND'""")
        for inv_id, state in cr.fetchall():
            ai_obj.action_cancel(cr, uid, [inv_id])
            try:
                ai_obj.action_cancel_draft(cr, uid, [inv_id])
                if state<>'draft':
                    wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_clp_error.txt",'a')
                fo1.write(str(inv_id)+"-")
                fo1.close()
                continue
        return True
    
    def update_client_payment(self, cr, uid, ids, context):
         # Tat cac Client Payment ko o trang thai cancel
         # O trang thai Draft: convert Cancel -> Draft (1)
         # O trang thai Open: (1), Workflow invoice_proforma2 button (2)
         # O trang thai Paid: (1), Workflow invoice_open button (3)
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                            ai.id,
                            curr_state,
                            rc.name,
                            tax_base
                        from
                            account_invoice ai
                        left join
                            res_currency rc on currency_id=rc.id
                        where
                            curr_state not in ('cancel') and state='cancel'""")        
        ai_obj = self.pool.get('account.invoice')
        ai_ids=[]
        loop=0
        fo=open("/home/openerp/processed_clp.txt",'w')
        fo.write(" ")
        fo.close()

        fo1=open("/home/openerp/processed_clp_error.txt",'w')
        fo1.write("")
        fo1.close()

        list_kpfc=[]
        for inv_id,state,curr_name,tb in cr.fetchall():
            list_kpfc.append((inv_id,state,curr_name,tb))
        
        for inv_id,state,curr_name,tb in list_kpfc:
            try:
                ai_obj.write(cr, uid, inv_id, {'tax_base':tb})
                ai_obj.action_cancel_draft(cr, uid, [inv_id])
                
                if state<>'draft':
                    wf_service.trg_validate(uid, 'account.invoice', inv_id, 'invoice_open', cr)
                fo1=open("/home/openerp/processed_clp.txt",'a')
                fo1.write(str(inv_id)+"-")
                fo1.close()
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_clp_error.txt",'a')
                fo1.write(str(inv_id)+"-")
                fo1.close()
                continue
        return True
    
    def update_pol_draft(self, cr, uid, ids, context):
        cr.execute("""select 
                        max(pol.id),
                        order_id 
                    from 
                        purchase_order_line pol 
                    left join
                        purchase_order po on pol.order_id=po.id
                    where
                        po.state='draft'
                    group by
                        order_id""")
        pol_ids=[]
        for pol_id,po_id in cr.fetchall():
            pol_ids.append(pol_id)
        self.pool.get('purchase.order.line').write(cr, uid, pol_ids,{})
        
        cr.execute("""Update
                             purchase_order po 
                        set 
                            amount_untaxed=coalesce(amount_untaxed,0),
                            final_price=coalesce(final_price,0),
                            discount_percent=coalesce(discount_percent,0),
                            amount_total=coalesce(amount_total,0) where state='draft'""")
        return True
    
    
    
    def update_pol_temp(self, cr, uid, ids, context):
        cr.execute("""Update purchase_order_line set budget_id=pp.budget_id from product_product pp where product_id=pp.id""")
        cr.execute("""select 
                        max(pol.id),
                        order_id 
                    from 
                        purchase_order_line pol 
                    left join
                        purchase_order po on pol.order_id=po.id
                    group by
                        order_id""")
        pol_ids=[]
        po_ids=[]
        for pol_id,po_id in cr.fetchall():
            self.pool.get('purchase.order.line').write(cr, uid, [pol_id],{})
            cr.commit()
          
        fo1=open("/home/openerp/processed_poltemp_error.txt",'w')
        fo1.write("")
        fo1.close()

        cr.execute("""Select 
                        distinct
                        id,
                        discount_amount
                    from 
                        purchase_order pol""")
        for order_id,da in cr.fetchall():
            try:
                self.pool.get('purchase.order').write(cr, uid, [order_id], {'discount_amount':da})
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_poltemp_error.txt",'a')
                fo1.write(str(order_id)+"$-")
                fo1.close()
        return True
    
    def update_pol_temp2(self, cr, uid, ids, context):
    
        cr.execute("""select expense_id,discount_amount from kderp_expense_budget_line left join purchase_order po on expense_id=po.id where coalesce(budget_id,0)=0 and expense_obj='purchase.order'""")
          
        fo1=open("/home/openerp/processed_poltemp2_error.txt",'w')
        fo1.write("")
        fo1.close()

        for order_id,da in cr.fetchall():
            try:
                self.pool.get('purchase.order').write(cr, uid, [order_id], {'discount_amount':da})
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_poltemp2_error.txt",'a')
                fo1.write(str(order_id)+"$-")
                fo1.close()
        return True
    
    
    def update_pol_temp3(self, cr, uid, ids, context):
    
        cr.execute("""Select id,
                            discount_amount from purchase_order where coalesce(amount_untaxed,0)=0""")
          
        fo1=open("/home/openerp/processed_poltemp3_error.txt",'w')
        fo1.write("")
        fo1.close()

        for order_id,da in cr.fetchall():
           
            self.pool.get('purchase.order').write(cr, uid, [order_id], {'discount_amount':da})
            cr.commit()
        return True
    
#     def update_po_amount(self, cr, uid, ids, context):
#          # Tat cac Client Payment ko o trang thai cancel
#          # O trang thai Draft: convert Cancel -> Draft (1)
#          # O trang thai Open: (1), Workflow invoice_proforma2 button (2)
#          # O trang thai Paid: (1), Workflow invoice_open button (3)
#         res = {}
#         wf_service = netsvc.LocalService("workflow")
#         
#         cr.execute("""Select 
#                             po.id,
#                             discount_amount
#                         from
#                             purchase_order po
#                         where
#                            state<>'cancel'""")        
#         po_obj = self.pool.get('purchase.order')
#         po_ids=[]
#         for po_id,discount_amount in cr.fetchall():
#             if discount_amount:
#                 po_obj.write(cr, uid, [po_id], {'discount_amount':discount_amount})
#             else:
#                 po_ids.append(po_id)
#             cr.commit()
#         po_obj.write(cr, uid, [po_id], {'discount_amount':0})
#             
#         return True
    
    def update_po(self, cr, uid, ids, context):
         # Tat cac Client Payment ko o trang thai cancel
         # O trang thai Draft: convert Cancel -> Draft (1)
         # O trang thai Open: (1), Workflow invoice_proforma2 button (2)
         # O trang thai Paid: (1), Workflow invoice_open button (3)
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                            po.id,
                            curr_state
                        from
                            purchase_order po
                        where
                            exists(Select id from purchase_order_line pol where order_id=po.id) and curr_state not in ('cancel') and state='cancel'""")        
        po_obj = self.pool.get('purchase.order')
        po_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_po_error.txt",'w')
        fo1.write("")
        fo1.close()
        fo1=open("/home/openerp/processing_po.txt",'w')
        fo1.write("")
        fo1.close()
        
        for po_id,curr_state in cr.fetchall():
            try:
                po_obj.write(cr, uid, [po_id], {'tax_baseline':False})
                if curr_state=='done':
                    po_obj.action_done_revising(cr, uid, [po_id])
                    po_obj.action_revising_done(cr, uid, [po_id])
                elif curr_state=='waiting_for_payment':
                    po_obj.action_cancel_draft(cr, uid, [po_id])
                    wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_draft_final_quotation', cr)
                    wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_final_quotation_roa_completed', cr)
                    wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_roa_completed_delivered', cr)
                elif curr_state=='waiting_for_delivery':
                    po_obj.action_cancel_draft(cr, uid, [po_id])
                    wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_draft_final_quotation', cr)
                    wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_final_quotation_roa_completed', cr)
                elif curr_state=='waiting_for_roa':
                    po_obj.action_cancel_draft(cr, uid, [po_id])
                    wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_draft_final_quotation', cr)
                elif curr_state=='draft':
                    po_obj.action_cancel_draft(cr, uid, [po_id])
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_po_error.txt",'a')
                fo1.write(str(po_id)+"-")
                fo1.close()
                cr.rollback()
                try:
                    wf_service.trg_delete(uid, 'purchase.order', po_id, cr)
                except:
                    continue
                continue
        return True
    
    def update_rop_pay_temp(self, cr, uid, ids, context):
        cr.execute("""Select id,state from kderp_supplier_payment_pay where state='draft'""")
        kp_obj = self.pool.get('kderp.supplier.payment.pay')
        loop=0
        for id,state in cr.fetchall():#amount,name,amount,name,
            kp_obj.write(cr, uid, [id],{'state':state})
            cr.commit()
        return True
    
    ####### ROP
    def update_rop_temp(self, cr, uid, ids, context):
        cr.execute("""Select id,currency_id from kderp_supplier_payment where currency_id<>24""")
        ksp_obj = self.pool.get('kderp.supplier.payment')
        loop=0
        for id,currency_id in cr.fetchall():#amount,name,amount,name,
            ksp_obj.write(cr, uid, [id],{'currency_id':currency_id})
            cr.commit()
        return True
    
    def update_rop1(self, cr, uid, ids, context):
        cr.execute("""Select id,amount,name,currency_id from kderp_supplier_payment where coalesce(number,0)=0 or name is null""")
        ksp_obj = self.pool.get('kderp.supplier.payment')
        loop=0
        for id,amount,name,currency_id in cr.fetchall():#amount,name,amount,name,
            loop+=1
            ksp_obj.write(cr, uid, [id],{'currency_id':currency_id,'amount':amount,'name':name})
            cr.commit()
        return True
    
    def update_rop2(self, cr, uid, ids, context):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                            ksp.id,
                            curr_state
                        from
                            kderp_supplier_payment ksp
                        where
                            curr_state not in ('cancel') and state='cancel'
                            and exists(Select id from kderp_supplier_payment_line kspl where supplier_payment_id=ksp.id)""")        
        ksp_obj = self.pool.get('kderp.supplier.payment')
        ksp_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_ksp_error.txt",'w')
        fo1.write("")
        fo1.close()
        fo1=open("/home/openerp/processing_ksp.txt",'w')
        fo1.write("")
        fo1.close()
        
        for ksp_id,curr_state in cr.fetchall():
            fo1=open("/home/openerp/processing_ksp.txt",'a')
            fo1.write(str(ksp_id)+"-")
            fo1.close()
            try:
                if curr_state=='paid':
                    ksp_obj.action_back_revising(cr, uid, [ksp_id])
                    ksp_obj.btn_action_revising_completed(cr, uid, [ksp_id],context)
                elif curr_state=='completed':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_draft_to_pr_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pr_checking_to_bc_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_bc_confirm', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pro_to_site', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pm_confirm', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_bod_confirm', cr)                    
                elif curr_state=='waiting_bod':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_draft_to_pr_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pr_checking_to_bc_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_bc_confirm', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pro_to_site', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pm_confirm', cr)                    
                elif curr_state=='bc_checked':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_draft_to_pr_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pr_checking_to_bc_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_bc_confirm', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pro_to_site', cr)
                elif curr_state=='bc_passed':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_draft_to_pr_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pr_checking_to_bc_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_bc_confirm', cr)                    
                elif curr_state=='submitting':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_draft_to_pr_checking', cr)
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_pr_checking_to_bc_checking', cr)
                elif curr_state=='pr_dept_checking':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment', ksp_id, 'btn_draft_to_pr_checking', cr)    
                elif curr_state=='draft':
                    ksp_obj.wkf_action_cancel_draft(cr, uid, [ksp_id])
                    
                cr.commit()
                
            except:
                fo1=open("/home/openerp/processed_ksp_error.txt",'a')
                fo1.write(str(ksp_id)+"-")
                fo1.close()
                cr.rollback()
                try:
                    wf_service.trg_delete(uid, 'kderp.supplier.payment', ksp_id, cr)
                except:
                    continue
                continue
        return True
    
    def update_rop3(self, cr, uid, ids, context):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                        ksp.id,
                        curr_state
                    from
                        kderp_supplier_payment ksp
                    where 
                        curr_state<>state and state='cancel' and exists(Select id from kderp_supplier_payment_line kspl where supplier_payment_id=ksp.id)""")        
        ksp_obj = self.pool.get('kderp.supplier.payment')
        ksp_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_ksp_error.txt",'w')
        fo1.write("")
        fo1.close()
        fo1=open("/home/openerp/processing_ksp.txt",'w')
        fo1.write("")
        fo1.close()
        
        for ksp_id,cu in cr.fetchall():
            #fo1=open("/home/openerp/processing_ksp.txt",'a')
            #fo1.write(str(ksp_id)+"-")
            #fo1.close()
            try:
                loop+=1
                ksp_obj.action_back_revising(cr, uid, [ksp_id])
                ksp_obj.btn_action_revising_completed(cr, uid, [ksp_id],{})
                
                cr.commit()
                
            except:
                fo1=open("/home/openerp/processed_ksp_error.txt",'a')
                fo1.write(str(ksp_id)+"-% $" )
                fo1.close()
                cr.rollback()
                try:
                    wf_service.trg_delete(uid, 'kderp.supplier.payment', ksp_id, cr)
                except:
                    continue
                continue
        return True
    
    def update_rop4(self, cr, uid, ids, context):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                        rop_id,amount
                    from
                        supplier_payment_tax_temp sptt
                    left join
                        kderp_supplier_payment ksp on rop_id =ksp.id where exists(Select id from kderp_supplier_payment_line kspl where supplier_payment_id=ksp.id)""")        
        ksp_obj = self.pool.get('kderp.supplier.payment')
        ksp_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_ksp_error.txt",'w')
        fo1.write("")
        fo1.close()
        fo1=open("/home/openerp/processing_ksp.txt",'w')
        fo1.write("")
        fo1.close()
        
        for ksp_id,amount in cr.fetchall():
            loop+=1
            ksp_obj.write(cr, uid, [ksp_id],{'amount':amount})
            if loop==100:
                loop=0
                cr.commit()
        return True
    ####### END OF ROP
    
    ### MIGRATE OE
    def update_koe1(self, cr, uid, ids, context):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""select
                        budget_id,
                        trim(array_to_string(array_agg(koel.id::text),' '))::text
                    from
                        kderp_other_expense_line koel
                    left join
                        kderp_other_expense koe on expense_id=koe.id
                    inner join
                        (Select 
                            max(koel.id) as max_id
                        from
                            kderp_other_expense_line koel
                        group by
                            expense_id) vwtemp on koel.id=max_id 
                        where coalesce(budgets,'')=''
                    group by budget_id""")        
        koel_obj = self.pool.get('kderp.other.expense.line')
        fo1=open("/home/openerp/processed_koe_error.txt",'w')
        fo1.write("")
        fo1.close()
        for b_id,koel_ids in cr.fetchall():
            if koel_ids.isdigit():
                koel_ids=[int(koel_ids)]
            else:
                koel_ids=list(eval(koel_ids.strip().replace(' ',',').replace(' ','')))
            try:
                koel_obj.write(cr, uid, koel_ids,{'budget_id':b_id})
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_koe_error.txt",'a')
                fo1.write(str(koel_ids)+"-% $" )
                fo1.close()
                cr.rollback()
                continue
        return True
    
    def update_koe2(self, cr, uid, ids, context):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        fo1=open("/home/openerp/processed_koe_error.txt",'w')
        fo1.write("")
        fo1.close()
        
        cr.execute("""select
                        id,
                        curr_state
                    from
                        kderp_other_expense koe
                    where 
                        exists(Select id from kderp_other_expense_line koel where expense_id=koe.id and
                        curr_state<>state and curr_state<>'cancel')""")        
        koe_obj = self.pool.get('kderp.other.expense')
        
        for koe_id,curr_state in cr.fetchall():
            try:
                if curr_state=='draft':
                    koe_obj.action_cancel_draft(cr, uid, [koe_id], context)
                elif curr_state=='waiting_for_payment':
                    #koe_obj.action_cancel_draft(cr, uid, [koe_id], context)
                    koe_obj.action_draft_to_waiting_for_payment(cr, uid, [koe_id], context)
                elif curr_state=='done':
                      koe_obj.action_revising_done(cr, uid, [koe_id], context)

                cr.commit()
                
            except:
                fo1=open("/home/openerp/processed_koe_error.txt",'a')
                fo1.write(str(koe_id)+"-% $" )
                fo1.close()
                cr.rollback()
                try:
                    wf_service.trg_delete(uid, 'kderp.other.expense', koe_id, cr)
                except:
                    continue
                continue
                
        return True
    
    def update_koe_tmp(self, cr, uid, ids, context):
         # Tat cac Client Payment ko o trang thai cancel
         # O trang thai Draft: convert Cancel -> Draft (1)
         # O trang thai Open: (1), Workflow invoice_proforma2 button (2)
         # O trang thai Paid: (1), Workflow invoice_open button (3)
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                            id,
                            date
                        from
                            kderp_other_expense po
                        where
                           currency_id<>24""")        
        koe_obj = self.pool.get('kderp.other.expense')
        
        for koe_id,date in cr.fetchall():
            koe_obj.write(cr, uid, [koe_id], {'date':date})
            cr.commit()
        return True
    
    
    ########### UPDATE KSPE
    def update_kspe1(self, cr, uid, ids, context):
        
        res = {}
        wf_service = netsvc.LocalService("workflow")
        
        cr.execute("""Select 
                            kspe.id,
                            curr_state
                        from
                            kderp_supplier_payment_expense kspe
                        where
                            curr_state not in ('cancel') and state='cancel'
                            and exists(Select id from kderp_supplier_payment_expense_line kspel where supplier_payment_expense_id=kspe.id)""")        
        kspe_obj = self.pool.get('kderp.supplier.payment.expense')
        kspe_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_kspe_error.txt",'w')
        fo1.write("")
        fo1.close()
        
        for kspe_id,curr_state in cr.fetchall():
            try:
                if curr_state in ('paid','completed'):
                    kspe_obj.action_back_revising(cr, uid, [kspe_id])
                    kspe_obj.btn_action_revising_completed(cr, uid, [kspe_id],context)
                elif curr_state=='waiting_bod':
                    kspe_obj.wkf_action_cancel_draft(cr, uid, [kspe_id])
                    wf_service.trg_validate(uid, 'kderp.supplier.payment.expense', kspe_id, 'btn_submit_confirm', cr)          
                elif curr_state=='draft':
                    kspe_obj.wkf_action_cancel_draft(cr, uid, [kspe_id])
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_kspe_error.txt",'a')
                fo1.write(str(kspe_id)+"-")
                fo1.close()
                cr.rollback()
                try:
                    wf_service.trg_delete(uid, 'kderp.supplier.payment.expense', kspe_id, cr)
                except:
                    continue
                continue
        return True
    
    def update_kspe2(self, cr, uid, ids, context):
        cr.execute("""update kderp_supplier_payment_expense set year=substring(name from 3 for 2)::int where coalesce(name,'')<>'';
                        update kderp_supplier_payment_expense set number=substring(name from 6 for 4)::int  where coalesce(name,'')<>'';""")
        res = {}
        cr.execute("""Select 
                            trim(array_to_string(array_agg(kspe.id::text),' '))::text,
                            currency_id
                        from
                            kderp_supplier_payment_expense kspe
                        where
                            state not in ('cancel')
                        group by
                            currency_id""")        
        kspe_obj = self.pool.get('kderp.supplier.payment.expense')
        kspe_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_kspe_error.txt",'w')
        fo1.write("")
        fo1.close()
        
        for kspe_ids,curr_id in cr.fetchall():
            if kspe_ids.isdigit():
                kspe_ids=[int(kspe_ids)]
            else:
                kspe_ids=list(eval(kspe_ids.strip().replace(' ',',').replace(' ','')))
                

            kspe_obj.write(cr, uid, kspe_ids,{'currency_id':curr_id})
            cr.commit()
        return True
    
    def update_kspe_ksp(self, cr, uid, ids, context):
        
        res = {}
        cr.execute(""" Select supplier_payment_expense_id from kderp_supplier_payment_expense_pay where currency_id=24 and exrate<>1""")        
        kspe_obj = self.pool.get('kderp.supplier.payment.expense')
        kspe_ids=[]
        loop=0
        fo1=open("/home/openerp/processed_kspe_curr_error.txt",'w')
        fo1.write("")
        fo1.close()
        
        for kspe_ids,curr_id in cr.fetchall():
            if kspe_ids.isdigit():
                kspe_ids=[int(kspe_ids)]
            else:
                kspe_ids=list(eval(kspe_ids.strip().replace(' ',',').replace(' ','')))
                

            kspe_obj.write(cr, uid, kspe_ids,{'currency_id':curr_id})
            cr.commit()
        return True
    
    #Update Asset Code
    def update_asset(self, cr, uid, ids, context):
#         cr.execute("""    Select id,
#                                     asset_code_id,
#                                     type_asset_id,
#                                     PODate
#                         from
#                                 (
#                                 Select 
#                                     id,
#                                     asset_code_id,
#                                     type_asset_id,
#                                     DateOfPurchase as PODate
#                                 from 
#                                     kderp_asset_management 
#                                 where 
#                                     dateofpurchase is not null
#                                 Union
#                                 Select 
#                                     id,
#                                     asset_code_id,
#                                     type_asset_id,
#                                     PODate
#                                 from 
#                                     kderp_asset_management kam
#                                 inner join
#                                     (Select 
#                                         assetnumber,
#                                         min(usedtime) as PODate
#                                     from 
#                                         u_dataassetusage  kam
#                                     where assetnumber in (
#                                     Select 
#                                         old_code
#                                     from 
#                                         kderp_asset_management 
#                                     where 
#                                         dateofpurchase is null) and usedtime is not null
#                                     group by 
#                                         assetnumber) vwfind on old_code=assetnumber) vwcombine
#                                 Order by
#                                     podate""")
        cr.execute("Select id from kderp_asset_management where coalesce(price,0)>0 and dateofinvoice is not null order by dateofinvoice,old_code")
        kam_obj=self.pool.get('kderp.asset.management')
        kam_ids=[]
        for kam_id in cr.fetchall():            
            for kam in kam_obj.browse(cr, uid, [kam_id[0]]):
                #(self,cr, uid, ids, tangible, asset_code, code, price, date=time):
                #for id, asset_code_id,type_asset_id,PODate in cr.fetchall():tangible, asset_code, code, price, date=time
                #try:
                new_code=kam_obj.get_new_code(cr, uid, [], kam.type_asset_acc_id.id,kam.asset_code_id.id, '',kam.price,kam.dateofinvoice)['value']['code']
                #except:
                 #   raise osv.except_osv("E",kam_obj.get_new_code(cr, uid, [], kam.type_asset_acc_id.id,kam.asset_code_id.id, '',kam.price,kam.dateofpurchase))
                kam_obj.write(cr, uid,[kam.id],{'code':new_code,'type_asset_acc_id':kam.type_asset_acc_id.id})
                cr.commit()
        return True
    
    def update_asset_line(self, cr, uid, ids, context):
        cr.execute("""Select max(id) from kderp_asset_management_usage group by asset_management_id""")
        
        kamu_obj=self.pool.get('kderp.asset.management.usage')
        for idl in cr.fetchall():
            kamu_obj.write(cr, uid,[idl[0]],{})
            cr.commit()
        return True
    
    def update_asset_software(self, cr, uid, ids, context):
        cr.execute("""Select id from kderp_asset_management where needupdate and dateofpurchase is not null order by dateofpurchase,old_code""")
        
        kam_obj=self.pool.get('kderp.asset.management')
        
        for kam_id in cr.fetchall():            
            for kam in kam_obj.browse(cr, uid, [kam_id[0]]):
                #(self,cr, uid, ids, tangible, asset_code, code, price, date=time):
                #for id, asset_code_id,type_asset_id,PODate in cr.fetchall():tangible, asset_code, code, price, date=time
                new_code=kam_obj.get_new_code(cr, uid, ids, kam.type_asset_acc_id.id,kam.asset_code_id.id, '',kam.price,kam.dateofpurchase)['value']['code']
                
                kam_obj.write(cr, uid,[kam.id],{'code':new_code})
                cr.commit()
        return True
    
    def update_ia(self, cr, uid, ids, context):
        ia_obj = self.pool.get('ir.attachment')
        cr.execute("""Select id from ir_attachment""")
        ia_ids=[]
        for id in cr.fetchall():
            ia_ids.append(id[0])
        for ia_list in ia_obj.browse(cr, uid, ia_ids):
            ia_obj.write(cr, uid, [ia_list.id],{'datas':ia_list.datas})
            cr.commit()
            
        return True
    
    def update_ia_check(self, cr, uid, ids, context):
        ia_obj = self.pool.get('ir.attachment')
        cr.execute("""Select 
                        max(id),
                        res_model,
                        res_id 
                    from 
                        ir_attachment
                    group by
                        res_model,
                        res_id""")
        fo1=open("/home/openerp/processed_ia_error.txt",'w')
        fo1.write("")
        fo1.close()
        for id_att,res_model,res_id in cr.fetchall():
            try:
                ia_obj.write(cr, uid, [id_att],{'res_model':res_model,'res_id':res_id})
                cr.commit()
            except:
                fo1=open("/home/openerp/processed_ia_error.txt",'a')
                fo1.write(res_model)
                fo1.write("-")
                fo1.write(str(res_id))
                fo1.write("\n")
                fo1.close()
        return True
    
kderp_migrate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
