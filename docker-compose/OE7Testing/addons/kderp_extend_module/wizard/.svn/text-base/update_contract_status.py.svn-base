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

from osv import fields
from osv import osv

import netsvc
import pooler
import time

import sys,os
from tools import config
import pooler
import base64

class kderp_update_contact_status(osv.osv_memory):
    _name='kderp.update.contact.status'
    _description = "KDERP Update Contract status"
    
    def update_contract_status(self, cr, uid, ids=False, context=False):
        #Status is Completed, Oustanding is None
        cr.execute("""Update kderp_contract_client kcc set 
                            state='completed',
                            outstanding='none'
                    where
                         (availability='cancelled' and coalesce(state,'')<>'completed') or
                        (coalesce(state,'')<>'completed' and
                        exists(Select id from account_invoice ai where contract_id=kcc.id and ai.state='paid') and
                        (coalesce(attached_approved_quotation,False)=True or coalesce(attached_contract_received,False)=True) and
                        kcc.id not in (Select
                                            contract_id 
                                        from 
                                            account_invoice ai
                                        where
                                            ai.state in ('open','draft') or
                                            (ai.state<>'cancel' and coalesce(pes_not_available,False)=False and coalesce(pes_cannot_collect,False)=False and coalesce(attached_progress_received,False)=False and coalesce(contract_id,0)=kcc.id) 
                                        ) and
                        kcc.id not in (Select 
                                            kcc.id
                                        from 
                                            kderp_contract_client kcc
                                        left join
                                            (Select
                                            kpfc.contract_id,
                                            sum(coalesce(kpvi.amount,0)+coalesce(diff_exrate,0)) as total_vat_amount
                                            from
                                            account_invoice kpfc
                                            left join
                                            kderp_payment_vat_invoice kpvi on kpfc.id = kpvi.payment_id
                                            left join
                                            kderp_contract_client kcc on contract_id=kcc.id
                                            where
                                            kpfc.state<>'cancel' 
                                            group by contract_id) vwpayment_vat on kcc.id = vwpayment_vat.contract_id
                                        where 
                                            total_vat_amount!=contracted_total
                                            or contracted_total!=contract_collect_total))""")
        
        #Status is UnCompleted, Outstanding is BC_Check
        cr.execute("""Update 
                        kderp_contract_client kcc
                      set 
                          state='uncompleted',outstanding='bc_check' 
                        where
                            (state='uncompleted' and outstanding<>'bc_check') and
                            coalesce(availability,'')<>'cancelled' and                            
                            id not in 
                                (Select 
                                    distinct kpfc.contract_id
                                from 
                                    account_invoice kpfc
                                left join 
                                    kderp_client_payment_term kptl on kpfc.payment_term_id = kptl.id 
                                where 
                                    kpfc.state<>'cancel' and
                                    due_date<=current_date and state ='draft' and
                                    kpfc.contract_id=kcc.id) and
                                (    
                                not exists(Select id from account_invoice kpfc where  kpfc.state='paid' and kpfc.contract_id = kcc.id limit 1) or
                                not (coalesce(attached_approved_quotation,False)=True or coalesce(attached_contract_received,False)=True) or
                                kcc.id in (Select
                                            contract_id 
                                        from 
                                            account_invoice kpfc
                                        where 
                                            kpfc.state<>'cancel' and
                                            (coalesce(pes_not_available,False)=False and coalesce(pes_cannot_collect,False)=False and coalesce(attached_progress_received,False)=False) and coalesce(contract_id,0)>0 
                                            and contract_id=kcc.id) 
                                or
                                kcc.id in 
                                    (Select 
                                        kccs.id
                                    from 
                                        kderp_contract_client kccs
                                    left join
                                        (Select
                                            kpfc.contract_id,
                                            sum(coalesce(kpvi.amount,0)+coalesce(diff_exrate,0)) as total_vat_amount
                                        from
                                            account_invoice kpfc
                                        left join
                                            kderp_payment_vat_invoice kpvi on kpfc.id = kpvi.payment_id
                                        left join
                                            kderp_contract_client kcc on contract_id=kcc.id
                                        where
                                            kpfc.state<>'cancel' and
                                            coalesce(kcc.state,'uncompleted')<>'completed'
                                        group by contract_id) vwpayment_vat on kcc.id = vwpayment_vat.contract_id
                                    where 
                                        kccs.id=kcc.id and (
                                        total_vat_amount!=contracted_total
                                        or contracted_total!=contract_collect_total)
                                        ));""")
        
        #Status is UnCompleted, Oustanding is PM_Check
        cr.execute("""Update kderp_contract_client kcc
                      set 
                          state='uncompleted',outstanding='pm_check' 
                        where 
                            (state='uncompleted' and outstanding<>'pm_check') and
                            coalesce(availability,'')<>'cancelled' and
                            id in 
                                (Select 
                                    distinct kpfc.contract_id 
                                 from 
                                    account_invoice kpfc
                                 left join 
                                    kderp_client_payment_term kptl on kpfc.payment_term_id = kptl.id  
                                 where 
                                     kpfc.contract_id=kcc.id and
                                     kpfc.state<>'cancel' and
                                    due_date<=current_date and state ='draft' and due_date is not null) and 
                            not (coalesce(attached_approved_quotation,False)=True or coalesce(attached_contract_received,False)=True);""")
        return True
kderp_update_contact_status()