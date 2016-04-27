# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

from openerp.tools import float_round

class kderp_create_progress_and_client_payment(osv.osv_memory):
    """KDERP Create Progress & Client Payment"""

    _name = "kderp.create.progress.and.client.payment"
    _description = "KDERP Create Progress and Client Payment"
    
    def _get_terms(self,cr,uid,context={}):
        if not context:
            context={}
        contract_id = context.get('contract_id',0)
        list_exist_contract=''
        
        if contract_id and context.get('typecreate','')=='client_payment':
            cr.execute("""Select 
                            kcpt.id,
                            name || ' ' || rtrim(ltrim(to_char(value_amount,'900.00%%')))
                        from 
                            kderp_client_payment_term kcpt
                        where 
                            contract_id=%s and 
                            id not in (Select payment_term_id from account_invoice ai where contract_id =%s)
                        Order by
                            sequence asc""" % (contract_id,contract_id))
        
            for ncode,nname in cr.fetchall():
                nname=nname.replace("'",'"')
                ncode=str(ncode)
                if list_exist_contract=='':
                    list_exist_contract="('"+ncode+"','"+nname+"')"
                else:
                    list_exist_contract=list_exist_contract+",('"+ncode+"','" + nname + "')"
            if list_exist_contract:
                list_exist_contract="["+ "('all','All Term')," + list_exist_contract + ",('none','None')" + "]"
                
        elif contract_id:
            cr.execute("""Select 
                            kcpt.id,
                            name || ' ' || rtrim(ltrim(to_char(value_amount,'900.00%%')))
                        from 
                            kderp_client_payment_term kcpt
                        where 
                            contract_id=%s and type='p'
                        Order by
                            sequence asc""" % (contract_id))
            Number = 0
            for ncode,nname in cr.fetchall():
                nname=nname.replace("'",'"')
                Number+=1
                ncode=str(ncode)
                nname=str(Number) + ". " + nname
                if list_exist_contract=='':
                    list_exist_contract="('"+ncode+"','"+nname+"')"
                else:
                    list_exist_contract=list_exist_contract+",('"+ncode+"','" + nname + "')"
                    
            if list_exist_contract:
                list_exist_contract="[" + list_exist_contract + ",('none','None')" + "]"
        if not list_exist_contract:
            list_exist_contract="[('none','None')]"
        return eval(list_exist_contract)
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context={}, toolbar=False, submenu=False):
        if not context:
            context={}
        return super(self.__class__,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
            
   
    _columns = {
                #'typetocreate':fields.selection([('pr_cp','Progress & Payment'),('pr','Progress'),('cp','Client Payment')],'Create',required=True),
                'payment_term_id':fields.selection(_get_terms,'Payment Term',required=True),
                'progress_no':fields.integer('No.')
               }
    _defaults={
                'payment_term_id':lambda *a:'all',
                'progress_no':lambda *a:1,
                }
    
    def create_client_payment(self, cr, uid, id, context):
        if not context:
            context={}
        
        term_create=self.read(cr,uid,id,['payment_term_id'])[0]['payment_term_id']
        
        ctc_obj = self.pool.get('kderp.contract.client')
        contract_id = context.get('contract_id',0)
        term_ids = []
        
        if term_create=='none':
            return True
        else:
            if term_create=='all':
                if contract_id and context.get('typecreate','')=='client_payment':
                    cr.execute("""Select 
                                    kcpt.id
                                from 
                                    kderp_client_payment_term kcpt
                                where 
                                    contract_id=%s and 
                                    id not in (Select payment_term_id from account_invoice ai where contract_id =%s)
                                Order by
                                    sequence asc""" % (contract_id,contract_id))
                    
                    for term_id in cr.fetchall():
                        term_ids.append(term_id[0])
            else:
                term_ids = [int(term_create)]
        
        str_term_ids = ",".join(map(str,term_ids))
        pfc_obj=self.pool.get('account.invoice')
        kur_obj = self.pool.get('kderp.contract.currency')
        acc_obj=self.pool.get('account.account')
        
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_currency_id = user.company_id.currency_id.id
        #cp_invoice_ids=[]
        for ctc in ctc_obj.browse(cr, uid, [contract_id], context):
            if ctc.payment_term_ids:                
                #raise osv.except_osv("E",pfc_obj.search(cr,uid, [('contract_id', '=', ctc.id),('payment_term_line_id','in',term_ids)]))
                if pfc_obj.search(cr,uid, [('contract_id', '=', ctc.id),('payment_term_id','in',term_ids)]):
                    raise osv.except_osv("Error","Payment already exist !")
                else:
                    
                    result={}
                    
                    #Tax Per
                    tax_ids = []
                    
                    payment_lists = []
                    
                    result['number'] = False
                    
                    if ctc.client_id:
                        result['partner_id'] = ctc.client_id.id
                    else:
                        result['partner_id'] = False
                        
                    if ctc.owner_id:
                        result['owner_id'] = ctc.owner_id.id
                    else:
                        result['owner_id'] = False
                        
                    if ctc.address_id:
                        result['address_id'] = ctc.address_id.id
                    else:
                        result['address_id'] = False
                        
                    if ctc.invoice_address_id:
                        result['invoice_address_id'] = ctc.invoice_address_id.id
                    else:
                        result['invoice_address_id'] = False

                    result['contract_id']=ctc.id
                    result['period_id']=ctc.period_id.id
                       # result['contract_currency_id']=ctc.contract_currency.id
                    #And Job Info to jobs_detail
                    
                    cr.execute("""Select 
                                    kcc.contract_id,
                                    kcc.name as from_currency_id,
                                    kcc.name as to_currency_id,
                                    account_analytic_id,
                                    amount_currency,
                                    True as Converted,
                                    aaa.code || '- ' || aaa.name
                                from 
                                    kderp_contract_currency kcc
                                left join
                                    kderp_quotation_contract_project_line kqcpl on kcc.contract_id = kqcpl.contract_id and kcc.name=kqcpl.currency_id
                                left join
                                    account_analytic_account aaa on account_analytic_id=aaa.id
                                where 
                                    coalesce(account_analytic_id,0)>0 and coalesce(default_curr,False)=True and kcc.contract_id=%s
                                Union
                                Select 
                                    kcc.contract_id,
                                    kcc.name as from_currency_id,
                                    coalesce((Select 
                                        name
                                    from 
                                        kderp_contract_currency 
                                    where
                                        contract_id=kcc.contract_id and coalesce(special_curr,False)=True),0) as to_currency_id,
                                    account_analytic_id,
                                    amount_currency,
                                    False as Converted,
                                    aaa.code || '- ' || aaa.name
                                from 
                                    kderp_contract_currency kcc
                                left join
                                    kderp_quotation_contract_project_line kqcpl on kcc.contract_id = kqcpl.contract_id and kcc.name=kqcpl.currency_id
                                left join
                                    account_analytic_account aaa on account_analytic_id=aaa.id
                                where 
                                    coalesce(account_analytic_id,0)>0 and coalesce(default_curr,False)=False and kcc.contract_id=%s;""" %(ctc.id,ctc.id))
                    
                    job_contract_summary = cr.fetchall()
                    jobs_detail = {}
                    for contract_id,from_currency_id,to_currency_id,account_analytic_id,amount,converted,job_name in job_contract_summary:
                        if not converted:
                            amount = kur_obj.compute(cr, uid, from_currency_id, to_currency_id, contract_id ,amount)
                        if '%s-%s-%s' % (contract_id,to_currency_id,account_analytic_id) in jobs_detail:
                            original_amount = jobs_detail['%s-%s-%s' % (contract_id,to_currency_id,account_analytic_id)]['amount']                           
                            jobs_detail['%s-%s-%s' % (contract_id,to_currency_id,account_analytic_id)]['amount']= original_amount + amount
                        else:
                            jobs_detail['%s-%s-%s' % (contract_id,to_currency_id,account_analytic_id)]={'adv_amount':0.0,
                                                                                                      're_amount':0.0,
                                                                                                      'amount':amount,
                                                                                                      'currency_id':to_currency_id,'account_analytic_id':account_analytic_id,
                                                                                                      'job_name':job_name}
                    job_contract_summary = jobs_detail.copy()
                            
                    for curr_line in ctc.contract_summary_currency_ids:
                        curr_id = curr_line.name.id
                        curr_name = curr_line.name.name
                        #raise osv.except_osv("E",(curr_name))
                        payment_detail = []
                        ctc_total_amount = curr_line.amount
                        tax_id = curr_line.tax_id
                        
                        tax_ids = [(6,0,[t_id.id for t_id in curr_line.tax_id])]
                        
                        result['currency_id'] = curr_id
                        result['exrate'] = 1 if curr_id==company_currency_id else 0.0
                        
                        result['invoice_line'] = payment_detail
                        
                        adv = 0.0
                        retention = 0.0
                        progress_amount = 0.0
                        vat_tax_amount = 0.0
                        ctc_amount_wh_tax = 0.0
                        
                        tmp_adv_vat = False
                        tmp_adv = 0
                        
                        tmp_re_vat = False
                        tmp_retention = 0
                        tmp_progress = 0
                        
                        if ctc_total_amount>0:
                            for pml in ctc.payment_term_ids:
                                if pml.type=='adv':
                                    if pml.tax_include:
                                        tmp_adv_vat=True
                                        
                                    for job_obj in jobs_detail:
                                        #jobs_detail[job_obj][curr_name].update({'adv_amount':jobs_detail[job_obj][curr_name]['adv_amount']+jobs_detail[job_obj][curr_name]['amount']*pml.value_amount / 100.0})
                                        if jobs_detail[job_obj]['currency_id']==curr_id:
                                            job_adv_amount = jobs_detail[job_obj]['adv_amount']
                                            
                                            job_amount = jobs_detail[job_obj]['amount']
                                            job_amount_term = job_amount*pml.value_amount / 100.0
                                            job_amount_term = float_round(job_amount_term,precision_rounding=curr_line.name.rounding)
                                            
                                            jobs_detail[job_obj].update({'adv_amount':job_adv_amount+job_amount_term})
                                        
                                    #result['amount'] =  0.0
                                    per_in_text = str(pml.value_amount) + "% "
                                    if pml.name.find("%")<0:
                                        result['name'] = pml.name #+ " " + per_in_text +  (ctc.project_name or "")
                                    else:
                                        result['name'] = pml.name #+ " " +  (ctc.project_name or "")
                                    
                                    #result['name'] = ctc.description
                                    result['payment_term_id'] = pml.id
                                    
                                    cal_amount =ctc_total_amount * pml.value_amount / 100.0 #Advanced
                                    #result['adv_payment'] =  float_round(cal_amount,precision_rounding=curr_line.name.rounding)                                                    
                                   # result['retention'] = 0.0
                                    
                                    if tmp_adv_vat:
                                        result['tax_base']='p_adv'
                                        
                                    tmp_adv = tmp_adv + cal_amount
                                    
                                    payment_detail = []
                                    if pml.id in term_ids:
                                        for ctc_prj in job_contract_summary:
                                            if job_contract_summary[ctc_prj]['currency_id']==curr_line.name.id:
                                                adv_amount = float_round(job_contract_summary[ctc_prj]['amount']*pml.value_amount / 100.0,precision_rounding=curr_line.name.rounding)
                                                amount = 0.0
                                                re_amount = 0.0
                                                payment_detail.append((0,0,{'account_analytic_id':job_contract_summary[ctc_prj]['account_analytic_id'],
                                                                            'name':job_contract_summary[ctc_prj]['job_name'],
                                                                            'advanced':adv_amount,
                                                                            'retention':re_amount,
                                                                            'amount':amount,
                                                                            'invoice_line_tax_id':tax_ids if tmp_adv_vat else False}))
                                        result['invoice_line'] = payment_detail
                                        payment_lists.append(result.copy())
                                    
                                elif pml.type =='re':
                                    if pml.tax_include:
                                        tmp_re_vat=True
                                        
                                    #result['amount'] =  0.0
                                    
                                    per_in_text = str(pml.value_amount) + "% "
                                    if pml.name.find("%")<0:
                                        result['name'] = pml.name #+ " " + per_in_text +  (ctc.project_name or "")
                                    else:
                                        result['name'] = pml.name #+ " " +  (ctc.project_name or "")
                                    
                                    result['payment_term_id'] = pml.id
                                    
                                    if tmp_re_vat:
                                        result['tax_base']='p_retention'
                                        
                                    for job_obj in jobs_detail:
                                        if jobs_detail[job_obj]['currency_id']==curr_id:
                                            job_re_amount = jobs_detail[job_obj]['re_amount']
                                            
                                            job_amount = jobs_detail[job_obj]['amount']
                                            job_amount_term = job_amount*pml.value_amount / 100.0
                                            job_amount_term = float_round(job_amount_term,precision_rounding=curr_line.name.rounding)
                                            
                                            jobs_detail[job_obj].update({'re_amount':job_re_amount+job_amount_term})

                                    cal_amount = ctc_total_amount * pml.value_amount / 100.0 #Retention
                                    #result['retention'] = float_round(cal_amount,precision_rounding=curr_line.name.rounding)
                                    #result['adv_payment'] = 0.0
                                    tmp_retention = tmp_retention + cal_amount
                                    
                                    payment_detail = []
                                    if pml.id in term_ids:
                                        for ctc_prj in job_contract_summary:
                                            if job_contract_summary[ctc_prj]['currency_id']==curr_line.name.id:
                                                re_amount = float_round(job_contract_summary[ctc_prj]['amount']*pml.value_amount / 100.0,precision_rounding=curr_line.name.rounding)
                                                amount = 0.0
                                                adv_amount = 0.0
                                                payment_detail.append((0,0,{'account_analytic_id':job_contract_summary[ctc_prj]['account_analytic_id'],
                                                                            'name':job_contract_summary[ctc_prj]['job_name'],
                                                                            'advanced':adv_amount,
                                                                            'retention':re_amount,
                                                                            'amount':amount,
                                                                            'invoice_line_tax_id':tax_ids if tmp_re_vat else False}))
                                        result['invoice_line'] = payment_detail
                                        
                                        payment_lists.append(result.copy())
                            #raise osv.except_osv("E",jobs_detail)
                            for pml in ctc.payment_term_ids:                                
                                if pml.id in term_ids and pml.type not in ['adv','re']:
                                    if tmp_adv_vat and tmp_re_vat:
                                        result['tax_base']='all'
                                    elif tmp_adv_vat:
                                        result['tax_base']='p_adv'
                                    elif tmp_re_vat:
                                        result['tax_base']='p_retention'

                                    #result['amount'] =  0.0
                                    
                                    per_in_text = str(pml.value_amount) + "% "
                                    if pml.name.find("%")<0:
                                        result['name'] = pml.name #+ " " + per_in_text +  (ctc.project_name or "")
                                    else:
                                        result['name'] = pml.name #+ " " +  (ctc.project_name or "")
                                    #result['itemofrequest'] = pml.name  + " " +  ctc.project_name
                                    
                                    #result['name'] = ctc.description
                                    result['payment_term_id'] = pml.id
                                    
                                    #result['adv_payment']=0.0
                                    #result['retention']=0.0
                                    
                                    cal_amount = ctc_total_amount * pml.value_amount / 100.0 #Retention
                                    cal_amount = float_round(cal_amount,precision_rounding=curr_line.name.rounding)
                                    
                                    x_adv_payment = -float_round(tmp_adv * pml.value_amount / 100.0,precision_rounding=curr_line.name.rounding)
                                    x_retention = -float_round(tmp_retention * pml.value_amount / 100.0,precision_rounding=curr_line.name.rounding)
                                    claim_amount = cal_amount + x_adv_payment + x_retention
                                    
                                    #result['retention'] = x_retention
                                    #result['adv_payment'] = x_adv_payment
                                    #result['amount'] = cal_amount
                                    
                                    tax_amount = 0
                                    for tax in curr_line.tax_id:
                                        if tax.type=='percent':
                                            tax_amount+=float_round(cal_amount*tax.amount,precision_rounding=curr_line.rounding)
                                        elif tax.type=='fixed':
                                            tax_amount+=tax.amount
#                                     tax_line=[]
#                                     tax_line.append((0,0,{'name':'VAT','amount':tax_amount}))
#                                     result['tax_line'] = tax_line
                                    
                                    payment_detail = []
                                    for job_obj in job_contract_summary:
                                        if job_contract_summary[job_obj]['currency_id']==curr_id:
                                            total_job_amount = job_contract_summary[job_obj]['amount']
                                            job_cal_amount = float_round(total_job_amount * pml.value_amount / 100.0 ,precision_rounding=curr_line.name.rounding)
                                            job_x_adv_payment = - float_round(jobs_detail[job_obj]['adv_amount'] * pml.value_amount / 100.0 ,precision_rounding=curr_line.name.rounding)
                                            job_x_retention = - float_round(jobs_detail[job_obj]['re_amount'] * pml.value_amount / 100.0 ,precision_rounding=curr_line.name.rounding)
                                            
                                            #job_amount = job_cal_amount + job_x_adv_payment + job_x_retention
                                            payment_detail.append((0,0,{'account_analytic_id':job_contract_summary[job_obj]['account_analytic_id'],
                                                                        'name':job_contract_summary[job_obj]['job_name'],
                                                                        'invoice_line_tax_id':tax_ids,
                                                                        'advanced':job_x_adv_payment,
                                                                        'retention':job_x_retention,
                                                                        'amount':job_cal_amount}))
                                        
                                    result['invoice_line'] = payment_detail
                                        
                                    payment_lists.append(result.copy())
                    #raise osv.except_osv("E",payment_lists)

                    for pmt in payment_lists: 
                        new_invoice_id=pfc_obj.create(cr,uid,pmt,context={'type':'out_invoice'})
                        
            else:
                raise osv.except_osv("Error","Please check payment term for this job !")
        if contract_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Client Payment',
                'view_type': 'form',
                'target':'current',
                'nodestroy': True,
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'domain': "[('contract_id','=',%s)]" % contract_id
                }
        else:
            return True
    
    #Create Progress
    def create_progress_evaluation(self, cr, uid, id, context):
        if not context:
            context={}

        orm_memory =self.read(cr,uid,id,['payment_term_id','progress_no'])[0]
        term_create = orm_memory['payment_term_id']
        progress_no = orm_memory['progress_no']
        ctc_obj = self.pool.get('kderp.contract.client')
        contract_id = context.get('contract_id',0)
        term_ids = []
        
        if term_create=='none':
            return True
        else:
            if term_create=='all':
                if contract_id:
                    cr.execute("""Select 
                                    kcpt.id
                                from 
                                    kderp_client_payment_term kcpt
                                where 
                                    contract_id=%s and type='p'
                                Order by
                                    sequence asc""" % (contract_id))
                    
                    for term_id in cr.fetchall():
                        term_ids.append(term_id[0])
            else:
                term_ids = [int(term_create)]
        
        str_term_ids = ",".join(map(str,term_ids))
        progress_obj=self.pool.get('kderp.progress.evaluation')

        for ctc in ctc_obj.browse(cr, uid, [contract_id], context):
            if ctc.payment_term_ids:                
                    result={}
                    tax_ids = []
                    progress_lists = []

                    for curr_line in ctc.contract_summary_currency_ids:
                        curr_id = curr_line.name.id
                        curr_name = curr_line.name.name
                        #raise osv.except_osv("E",(curr_name))
                        payment_detail = []
                        ctc_total_amount = curr_line.amount
                        tax_id = curr_line.tax_id
                        
                        result['currency_id'] = curr_id
                        result['contract_id'] = ctc.id

                        adv = 0.0
                        retention = 0.0
                        progress_amount = 0.0
                        vat_tax_amount = 0.0
                        ctc_amount_wh_tax = 0.0
                        
                        tmp_adv_vat = False
                        tmp_adv = 0
                        tmp_retention = 0
                        
                        tmp_retention_vat = False
                        tmp_progress = 0
                        
                        if ctc_total_amount>0:
                            for pml in ctc.payment_term_ids:
                                if pml.type=='adv':
                                    if pml.tax_include:
                                        tmp_adv_vat=True
                                    cal_amount =ctc_total_amount * pml.value_amount / 100.0 #Advanced
                                    result['adv_payment'] =  float_round(cal_amount,precision_rounding=curr_line.name.rounding)                                                    
                                    result['retention'] = 0.0
                                    tmp_adv = tmp_adv + cal_amount
                                elif pml.type =='re':
                                    if pml.tax_include:
                                        tmp_retention_vat = True
                                    cal_amount = ctc_total_amount * pml.value_amount / 100.0 #Retention
                                    cal_amount = float_round(cal_amount,precision_rounding=curr_line.name.rounding)
                                    tmp_retention = tmp_retention + cal_amount
                        
                            for pml in ctc.payment_term_ids:                                
                                if pml.id in term_ids and pml.type not in ['adv','re']:
                                    
                                    cal_amount = ctc_total_amount * pml.value_amount / 100.0
                                    cal_amount = float_round(cal_amount,precision_rounding=curr_line.name.rounding)
                                    x_adv_payment = -float_round(tmp_adv * pml.value_amount / 100.0,precision_rounding=curr_line.name.rounding)
                                    x_retention = -float_round(tmp_retention * pml.value_amount / 100.0,precision_rounding=curr_line.name.rounding)

                                    tax_amount = 0
                                    tax_baseon = cal_amount
                                    if tmp_retention_vat:
                                        tax_baseon = tax_baseon + x_retention
                                    if tmp_adv_vat:
                                        tax_baseon = tax_baseon + x_adv_payment
                                        
                                    for tax in curr_line.tax_id:
                                        if tax.type=='percent':
                                            tax_amount+=float_round(tax_baseon*tax.amount,precision_rounding=curr_line.rounding)
                                        elif tax.type=='fixed':
                                            tax_amount+=tax.amount
                                    
                                    result['vat'] = tax_amount
                                    result['retention'] = x_retention
                                    result['advanced'] = x_adv_payment
                                    result['amount'] = cal_amount
                                    result['name'] = progress_no
                                    
                                    progress_lists.append(result.copy())
                                    
                    for pl in progress_lists:
                        progress_id=progress_obj.create(cr,uid,pl)
        return True
    
kderp_create_progress_and_client_payment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
