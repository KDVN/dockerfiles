# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class kderp_supplier_payment_batch_process(osv.osv_memory):

    _name = "kderp.supplier.payment.batch.process"
    _description = "KDERP Quotation Contract"
    
    def _get_state(self, cr, uid, context=None):
        if not context:
            context={}
        return context.get('state','draft')
    
    def _get_step(self, cr, uid, context=None):
        if not context:
            context={}
        payment_ids = context.get('active_ids',[])
        rop_ids = ",".join(map(str,payment_ids))
        table_payment={'kderp.supplier.payment':'kderp_supplier_payment',
                           'kderp.supplier.payment.expense':'kderp_supplier_payment_expense'}
        res_model = context.get('res_model',"")
        cr.execute("Select distinct state from %s where id in (%s)" % (table_payment[res_model],rop_ids))
        if cr.rowcount>1:
            raise osv.except_osv("KDERP Warning","You have to select expenses having the same state !")
        else:
            curr_state=cr.fetchone()[0]
            if curr_state in ['cancel','completed','paid']:
                raise osv.except_osv("KDERP Warning","Batch Work-flow doestn't work with status of Rejected; BOD Approved; Paid  !")
        
        
        if context.get('res_model',"")=='kderp.supplier.payment':
            steps = {'draft':1,
                    'pr_dept_checking':2,
                    'submitting':3,
                    'bc_passed':4,
                    'bc_checked':5,
                    'waiting_bod':6}
        else:
            steps = {'draft':10,
                    'waiting_bod':11}
        return steps[curr_state]           
    
    _columns={
              'state':fields.char('State',size=128,readonly=True),
              'step':fields.integer('Step',readonly=1),
              'next_step':fields.selection([('next_step','Next Step'),('from_site','Input From Site Date'),('to_pro_manager','To Procurement Manager Date'),('update_rop_date','Update R.O.P. Date')],'Next Step',required=1),              
              'date':fields.date("Date",required=1)
              }
    _defaults={
               'next_step': lambda *x:'next_step',
               'state':_get_state,
               'step':_get_step,
               'date': lambda *a: time.strftime('%Y-%m-%d'),
               }
    def onchange_next(self, cr, uid, ids,step, next_step):
        val={}
        warning = {}
        if step==1 and next_step not in ('next_step','update_rop_date'):
            warning = {  
              'title': _("KDERP Warning"),  
              'message': _('In this state you can select Next Step or Update ROP Date only !'),  
             }
            val={'next_step':False}
        elif step==5 and next_step in ('update_rop_date'):
            warning = {  
              'title': _("KDERP Warning"),  
              'message': _('In this state you can"t select Update ROP Date !'),  
             }
            val={'next_step':False}
        return {'value':val,'warning':warning}
        
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(kderp_supplier_payment_batch_process, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu=submenu)
        res_model = context.get('res_model',"")
        if res_model:
            payment_ids = context.get('active_ids',[])
            rop_ids = ",".join(map(str,payment_ids))
            global curr_state
            table_payment={'kderp.supplier.payment':'kderp_supplier_payment',
                           'kderp.supplier.payment.expense':'kderp_supplier_payment_expense'}
            
            cr.execute("Select distinct state from %s where coalesce(name,'')='' and id in (%s)" % (table_payment[res_model],rop_ids))
            if cr.rowcount>=1:
                raise osv.except_osv("KDERP Warning","Payment number must be valid !")
            
            cr.execute("Select distinct state from %s where id in (%s)" % (table_payment[res_model],rop_ids))
            
            if cr.rowcount>1:
                raise osv.except_osv("KDERP Warning","You have to select expenses having the same state !")
            else:
                curr_state=cr.fetchone()[0]
                if curr_state in ['cancel','completed','paid']:
                    raise osv.except_osv("KDERP Warning","Batch Work-flow doestn't work with status of Rejected; BOD Approved; Paid  !")
        return res
    
    
    def excute_action(self, cr, uid, ids, context={}):
        ksp_ids=context.get('active_ids',[])
        ksp_model=context.get('res_model','')
        ksp_obj=self.pool.get(ksp_model)
        wf_service = netsvc.LocalService("workflow")
        
        for kspbp in self.browse(cr, uid, ids):
            context['date']=kspbp.date
            step=kspbp.step
            if step>=10:
                if step==10:
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_submit_confirm', cr)
                else:
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_bod_confirm', cr)
            elif kspbp.next_step!='next_step' and kspbp.step==5 and kspbp.next_step!='update_rop_date':
                if kspbp.next_step=='from_site':
                    ksp_obj.write(cr,uid,ksp_ids,{'from_site_date':kspbp.date})
                else:
                    ksp_obj.write(cr,uid,ksp_ids,{'to_procurement_manager':kspbp.date})
            elif kspbp.next_step=='update_rop_date':
                if kspbp.step==1:
                    ksp_obj.write(cr,uid,ksp_ids,{'date':kspbp.date})
                else:
                    raise osv.except_osv("KDERP Warning","Update ROP Date, use in draft state only !")
            else:
                ksp_ids_str=",".join(map(str,ksp_ids))
                if step==1:
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_draft_to_pr_checking', cr)
                    cr.execute("Update kderp_supplier_payment set pro_to_acc='%s' where pro_to_acc is null and id in (%s)" % (kspbp.date,ksp_ids_str))
                elif step==2:#Pro. Checking -> BC Checking
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_pr_checking_to_bc_checking', cr)
                    cr.execute("Update kderp_supplier_payment set to_bc_date_first='%s' where to_bc_date_first is null and id in (%s)" % (kspbp.date,ksp_ids_str))
                elif step==3:#BC Checking -> BC Passed
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_bc_confirm', cr)
                    cr.execute("Update kderp_supplier_payment set bc_checked_date='%s' where bc_checked_date is null and id in (%s)" % (kspbp.date,ksp_ids_str))
                elif step==4:#BC Passed -> PM Checking
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_pro_to_site', cr)
                    cr.execute("Update kderp_supplier_payment set to_site_date='%s' where to_site_date is null and id in (%s)" % (kspbp.date,ksp_ids_str))
                elif step==5:#PM Checking -> BOD Checking
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_pm_confirm', cr)
                    cr.execute("Update kderp_supplier_payment set to_bc_date_second='%s' where to_bc_date_second is null and id in (%s)" % (kspbp.date,ksp_ids_str))
                elif step==6:#BOD Checking -> BOD Approved
                    cr.execute("Update kderp_supplier_payment set bc_to_accounting_date='%s' where bc_to_accounting_date is null and id in (%s)" % (kspbp.date,ksp_ids_str))
                    for rop_id in ksp_ids:
                        wf_service.trg_validate(uid, ksp_model, rop_id, 'btn_bod_confirm', cr)
        return {}

kderp_supplier_payment_batch_process()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

