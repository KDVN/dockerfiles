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
from osv import fields,osv
from osv.orm import except_orm
import tools

class kderp_wizard_packing_payment(osv.osv_memory):
    _name='kderp.wizard.packing.payment'
    _description='Create Supplier Payment to Packing'
    
    def supplier_payment_detail_create(self, job_id, amount, percent):
        return (0, False, {
                        'account_analytic_id':job_id,
                        'amount': amount*percent/100.0
                        })
            
    #Tao supplier Payment
    def create_packing_payment(self, cr, uid, ids, context):
        res = {}
        if context is None:
            context={}
        record_ids =  context.get('active_ids',[])
        if record_ids:
            res = []
            pay_obj = self.pool.get('stock.picking')
            
        ksp_ids=[]
        tmp_ids = ",".join(map(str,record_ids))
        
        cr.execute('Select id from stock_picking where coalesce(check_payment,0)>0 and id in (%s)' % tmp_ids)
        check_payment = cr.fetchone()
        if check_payment:
            raise osv.except_osv("KDERP Warning","One or more packing already created payment !")
        
        for po in pay_obj.browse(cr, uid, record_ids, context=context):
            if po.state in ('draft', 'cancel') or po.purchase_id.state in ('draft', 'cancel', 'done'):
                raise osv.except_osv("KDERP Warning","Check status Purchase and Packing !")
                        
            cr.execute("Select\
                                sum(coalesce(sm.product_qty,0)*(coalesce(pol.final_subtotal,0)/coalesce(pol.plan_qty,0))) as total_amount\
                        from\
                                stock_move sm\
                        left join\
                                purchase_order_line pol on purchase_line_id = pol.id\
                        where \
                                sm.picking_id in (%s)\
                        group by\
                                pol.order_id" % tmp_ids)
            tmp_one = cr.fetchone()
            if tmp_one:
                subtotal = tmp_one[0]
            adv_amount = 0.0
            retention_amount = 0.0
            
            for po_term in po.purchase_id.purchase_payment_term_ids:
                if po_term['type']=='adv':
                    adv_amount = po_term['value_amount']*subtotal/100
                    adv = po_term['value_amount']
                elif po_term['type']=='re':
                    retention_amount = po_term['value_amount']*subtotal/100
                    retention = po_term['value_amount']
                else:                    
                    progress = po_term['value_amount']
                this_progress_amount = subtotal
                this_adv_amount = - adv_amount
                this_retention_amount = - retention_amount
                
                tax_ids=[]
                for tax_id in po.purchase_id.taxes_id:
                    if (tax_id.type=='percent' or po_term.value_amount==100) and po_term.type=='p':
                        tax_ids.append(tax_id.id)
                        
                if po.purchase_id.notes:
                    new_description = po_term.name + "\n" + po.purchase_id.notes
                else:
                    new_description = ""
                
                payment_details = []
                cr.execute("Select\
                                pol.account_analytic_id,\
                                sum(coalesce(sm.product_qty,0)*(coalesce(pol.final_subtotal,0)/coalesce(pol.plan_qty,0)))\
                            from stock_move sm\
                            left join purchase_order_line pol on purchase_line_id = pol.id\
                            where pol.order_id=%s\
                            group by\
                                pol.account_analytic_id" % (po.purchase_id.id))
                for job_id,amount in cr.fetchall():
                    payment_details.append(self.supplier_payment_detail_create(job_id, amount, po_term.value_amount))
                                                              
                payment = {
                    'amount':this_progress_amount,
                    'taxes_id':[[6, False,tax_ids]],
                    'advanced_amount':this_adv_amount,
                    'retention_amount':this_retention_amount,
                    'currency_id': po.purchase_id.currency_id.id,
                    'payment_line': payment_details,
                    'order_id':po.purchase_id.id, 
                    'description':new_description#po_term['name'] + "\n"+  o['notes']
                }
    
                kderp_ksp_id = self.pool.get('kderp.supplier.payment').create(cr, uid, payment)
                cr.execute("Update stock_picking set check_payment=%d where id in (%s)" % (kderp_ksp_id,tmp_ids))
                ksp_ids.append(kderp_ksp_id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier Payment',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'kderp.supplier.payment',
            'domain': "[('id','in', ["+','.join(map(str,ksp_ids))+"])]"
            }
        

#kderp_wizard_packing_payment()

                
                