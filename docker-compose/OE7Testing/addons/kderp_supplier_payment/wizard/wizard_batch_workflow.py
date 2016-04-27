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

Form_Warning = '''
<form string="KDVN Warning">
    <separator string='' colspan="4"/>
</form>'''

Form_Warning2 = '''
<form string="KDVN Warning">
    <separator string=" colspan="4"/>
</form>'''

Form_Warning3 = '''
<form string="KDVN Warning">
    <separator string= colspan="4"/>
</form>'''
Fields=UpdateableDict()
Prepair_Form=UpdateableStr()
pts_ids = []
curr_state =''
step = 0
chk_type = ''

class kderp_supplier_payment_batch_process(osv.osv_memory):
    """KDERP Quotation Contract"""

    _name = "kderp.quotation.contract"
    _description = "KDERP Quotation Contract"
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(kderp_supplier_payment_batch_process, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu=submenu)
        
        global pts_ids, curr_state
        ids =[]
        if not context:
            context={}
            
        payment_ids = context.get('payment_ids',[])
        res_model = context.get('res_model',"")
                
        rop_ids = ",".join(map(str,payment_ids))
        
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
    
    def _prepair_form(self, cr, uid, data, context):
        global pts_ids, curr_state, step, chk_type
        Fields['date']={'string':'Date','type':'date','default': lambda *a:time.strftime('%Y-%m-%d')}
          
        #Fields['date_batch']={'string':'Batch Date','type':'date','default': lambda *a:time.strftime('%Y-%m-%d')}
        
        Fields['type_batch']={'string':'Type','type':'selection','selection':eval("[('next_step','Next Step'),('from_site','Input From Site Date'),('to_pro_manager','To Procurement Manager Date')]")}

        if curr_state=='draft':
            step = 1
            if chk_type=='IN':
                lbl='Draft-->Procurement Checking: &lt;Proceed&gt;'
            else:
                lbl='Draft-->BOD Checking: &lt;Submit to BOD&gt;'
        elif curr_state=='pr_dept_checking':
            step = 2
            lbl='Procurement Checking-->BC Checking: &lt;BC Received&gt;'
        elif curr_state=='submitting':
            step = 3
            lbl='BC Checking-->BC Checked: &lt;BC Checked&gt;'
        elif curr_state=='bc_passed':
            step = 4
            lbl='BC Checked-->PM Checking: &lt;Send to PM&gt;'
        elif curr_state=='bc_checked':
            step = 5
            lbl='PM Checking-->BOD Checking: &lt;PM Approved, Submit to BOD&gt;'
        else:
            step = 6
            lbl='BOD Checking-->BOD Approved: &lt;BOD Approved&gt;'
            
        if step<>5: 
            if chk_type=='IN' or step==6:  
                Prepair_Form.string='''<?xml version="1.0"?>
                    <form string="Batch Work-flow">
                        <separator string="'''+lbl+'''"/>
                        <field name="date"/>
                        <field name="type_batch" string='Batch Type' invisible='1' colspan="2"/>
                    </form>'''
            else:
                Prepair_Form.string='''<?xml version="1.0"?>
                    <form string="Batch Work-flow">
                        <separator string="'''+lbl+'''"/>
                        <field name="type_batch" string='Batch Type' invisible='1' colspan="2"/>
                    </form>'''
        else:
            Prepair_Form.string='''<?xml version="1.0"?>
                    <form string="Batch Process" colspan="4">
                        <group attrs="{'invisible':[('type_batch','!=','next_step')]}">
                            <separator string="'''+lbl+'''" colspan="4"/>
                        </group>
                        <group attrs="{'invisible':[('type_batch','!=','from_site')]}">
                            <separator string="Fill From Site Date" colspan="4"/>
                        </group>
                        <group attrs="{'invisible':[('type_batch','!=','to_pro_manager')]}">
                            <separator string="Fill To Procurement Date" colspan="4"/>
                        </group>
                        <group colspan="4" col="7">
                            <field name="type_batch" string='Batch Type' required='1' colspan="2"/>
                            <field colspan="2" name="date" required='1'/>
                        </group>
                    </form>'''
        return {}
    
    def _batch_workflow(self, cr, uid, data, context):
        global pts_ids, curr_state, step, chk_type
        
        pool = pooler.get_pool(cr.dbname)
        rop_obj = pooler.get_pool(cr.dbname).get('kdvn.request.of.payment')
        
        if data['form']['type_batch']!='next_step' and step==5:
            if data['form']['type_batch']=='from_site':
                rop_obj.write(cr,uid,pts_ids,{'from_site_date':data['form']['date']})
            else:
                rop_obj.write(cr,uid,pts_ids,{'to_procurement_manager':data['form']['date']})
        else:
            if chk_type=='IN':
                context['date']=data['form']['date']
            if step==1: #Draft -> Pro. Checking
                rop_obj.action_rop_draft_to_pr_checking(cr,uid,pts_ids,context)
            elif step==2:#Pro. Checking -> BC Checking
                rop_obj.action_rop_pr_checking_bc_checking(cr,uid,pts_ids,context)
            elif step==3:#BC Checking -> BC Passed
                rop_obj.action_rop_bc_confirm(cr,uid,pts_ids,context)
            elif step==4:#BC Passed -> PM Checking
                rop_obj.action_rop_send_to_pm(cr,uid,pts_ids,context)
            elif step==5:#PM Checking -> BOD Checking
                rop_obj.action_rop_pm_confirm(cr,uid,pts_ids,context)
            elif step==6:#BOD Checking -> BOD Approved
                rop_obj.action_rop_bod_confirm(cr,uid,pts_ids,context)
        return {}
        
    states = {
              'init': 
                      {
                       'actions': [],
                       'result': {'type': 'choice','next_state':_check}},
              'warning1': 
                      {
                        'actions': [],
                        'result': {
                                    'type': 'form','arch': Form_Warning,'fields':{},
                                    'state': [('end', '_Ok', 'gtk-ok', True)]}},
              'warning2': 
                      {
                        'actions': [],
                        'result': {
                                    'type': 'form','arch': Form_Warning2,'fields':{},
                                    'state': [('end', '_Ok', 'gtk-ok', True)]}},
              'warning3': 
                      {
                        'actions': [],
                        'result': {
                                    'type': 'form','arch': Form_Warning3,'fields':{},
                                    'state': [('end', '_Ok', 'gtk-ok', True)]}},
              'warning4': 
                      {
                        'actions': [],
                        'result': {
                                    'type': 'form','arch': Form_Warning4,'fields':{},
                                    'state': [('end', '_Ok', 'gtk-ok', True)]}},
              'next': 
                      {
                        'actions': [_prepair_form],
                        'result': {
                                   'type': 'form','arch': Prepair_Form,'fields':Fields,
                                   'state': 
                                            [('end', '_Cancel','gtk-cancel'),
                                             ('finish', '_Ok', 'gtk-ok', True),]}},
              'finish': 
                      {
                        'actions': [_batch_workflow],
                        'result': {
                                   'type': 'state',
                                   'state':'end'}},
              }
kderp_supplier_payment_batch_process()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

