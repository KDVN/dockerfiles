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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'Purchase Order'
    
    def _get_address_project_location(self, cr, uid, ids, name, args, context=None):
        res = {}
        if ids:
            po_ids = ",".join(map(str,ids))
            cr.execute("""select po.id as id , kpl.id  from 
                            purchase_order po 
                            left join kderp_project_location kpl 
                            on kpl.account_analytic_id=po.account_analytic_id
                            where po.id in (%s)
                               """ % (po_ids))
            for id,delivery_location_id in cr.fetchall():
                res[id]=delivery_location_id
        return res
  
    def action_expense_create_supplier_payment(self, cr, uid, ids, *args):
        res = {}
        #for o in self.browse(cr, uid, ids):
        ksp_ids=[]
        for po in self.browse(cr, uid, ids):
            payment_details = []
            adv_amount = 0.0
            retention_amount = 0.0
            adv = 0.0
            retention = 0.0
            progress = 0.0
            for po_term in po.purchase_payment_term_ids:
                if po_term.type=='adv':
                    adv_amount = po_term.value_amount*po.final_price/100.0
                    adv = po_term.value_amount
                elif po_term.type=='re':
                    retention_amount = po_term.value_amount*po.final_price/100.0
                    retention = po_term.value_amount
                else:                    
                    progress = po_term.value_amount
            for po_term in po.purchase_payment_term_ids:
                if po_term.type <>'p':
                    this_tax_amount = 0.0
                    this_progress_amount = 0.0
                    if po_term.type=='adv':
                        this_retention_amount = 0.0
                        this_adv_amount = adv_amount
                    else:
                        this_adv_amount = 0.0
                        this_retention_amount = retention_amount
                else:
                    progress = po_term.value_amount
                    this_tax_amount = po.amount_tax*po_term.value_amount/100.0
                    this_progress_amount = po.final_price*po_term.value_amount/100.0
                    this_adv_amount = - adv_amount*progress/100.0
                    this_retention_amount = - retention_amount*progress/100.0
                payment_details = []
                cr.execute("Select\
                                pol.account_analytic_id,\
                                sum(final_subtotal)\
                            from \
                                purchase_order_line pol\
                            where order_id=%s\
                            group by\
                                pol.account_analytic_id" % (po.id))
                for job_id,amount in cr.fetchall():
                    payment_details.append(self.supplier_payment_detail_create(job_id, amount, po_term.value_amount))
                    
                if po.notes:
                    new_description = po_term.name + "\n" + po.notes
                else:
                    new_description = ""
                
                tax_ids=[]
                for tax_id in po.taxes_id:
                    if (tax_id.type=='percent' or po_term.value_amount==100) and po_term.type=='p':
                        tax_ids.append(tax_id.id)
                                                             
                payment = {
                    'amount':this_progress_amount,
                    'taxes_id':[[6, False, tax_ids]],
                    'payment_type':'cash',
                    'advanced_amount':this_adv_amount,
                    'retention_amount':this_retention_amount,
                    'currency_id': po.currency_id.id,
                    'payment_line': payment_details,
                    'order_id':po.id, 
                    'description':new_description#po_term['name'] + "\n"+  o['notes']
                    }

                kderp_ksp_id = self.pool.get('kderp.supplier.payment').create(cr, uid, payment)
                ksp_ids.append(kderp_ksp_id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier Payment',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kderp.supplier.payment',
            'domain': "[('order_id','in',%s)]" % ids
            }                 
    _columns={
                'revision_no':fields.integer('Revision No.',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'receiver_id': fields.many2one('hr.employee', 'Receiver', select=1,ondelete='restrict'),
                #'general_contract_no':fields.char('G.C. No.',size=16),
                #'general_contract_date':fields.date('G.C. Date'),
                #'delivery_location_id':fields.function(_get_address_project_location, type='many2one', relation='kderp.project.location',method=True,string='Delivery Location'),
                'delivery_location_id':fields.many2one('kderp.project.location','Delivery Location',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),                                      
             }
    
    _defaults={
               'revision_no':lambda *x:0,              
               }
    
purchase_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

