# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
from lxml import etree
import openerp.addons.decimal_precision as dp

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = 'purchase.order'
    _description = "KDERP Purchase Order"
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if not context:
            context={}
        if context.get('kderp_search_po_over',False):
            cr.execute("""Select
                        distinct
                        po.id
                    from    
                        purchase_order po 
                    left join
                        purchase_order_line pol on po.id=order_id
                    left join
                        kderp_budget_data kbd on pol.budget_id=kbd.budget_id and pol.account_analytic_id=kbd.account_analytic_id
                    left join
                        kderp_expense_budget_line kebl on pol.budget_id=kebl.budget_id and pol.account_analytic_id=kebl.account_analytic_id and (date_order>kebl.date or (kebl.date=date_order and po.name>kebl.name))                         
                    Group by
                        po.id,
                        pol.id,
                        kbd.id
                    having
                        planned_amount-sum(coalesce(amount,0))<0""" )
            po_ids=[]
            for po_id in cr.fetchall():
                po_ids.append(po_id[0])                        
            args.append((('id', 'in', po_ids)))         
        return super(purchase_order, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)
    
    def _get_order_from_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    def _get_po_final_exrate(self, cr, uid, ids, name, args, context=None):#Tinh PO Final Exrate khi PO Completed
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        
        company_currency=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency_id=company_currency.id
        
        for po in self.browse(cr, uid, ids):
            if po.currency_id.id<>company_currency_id:
                paid_amount=0
                po_total_amount = po.amount_total
                for ksp in po.supplier_payment_ids:
                    if ksp.state not in ('draft','cancel'):
                        cal=False
                        for kp in ksp.payment_ids:
                            #if kp.state<>'draft':
                            cal=True
                            paid_amount+=cur_obj.round(cr, uid, company_currency, kp.amount*kp.exrate)
                        if cal:
                            po_total_amount-=ksp.total
                paid_amount+=cur_obj.compute(cr, uid, po.currency_id.id, company_currency_id, po_total_amount, round=True, context={'date':po.date_order})
                exrate=paid_amount/(po.amount_total*po.exrate) if (po.amount_total*po.exrate) else 0
                res[po.id]=exrate
            else:
                res[po.id]= 1
        return res            

    def check_and_make_po_done(self, cr, uid, ids, cron_mode=True, context=None):
        try:
            if not ids:
                ids = self.search(cr, uid, [('state','=','waiting_for_payment')])
            
            po_list_mark_done = []
            for po in self.browse(cr, uid, ids, context):
                if po.state=='waiting_for_payment':
                    if po.total_request_amount==po.total_vat_amount and po.total_vat_amount==po.total_payment_amount and po.total_payment_amount==po.amount_total:
                        po_list_mark_done.append(po.id)
                else:
                    continue
            wf_service = netsvc.LocalService("workflow")
            for po_id in po_list_mark_done:                
                wf_service.trg_validate(uid, 'purchase.order', po_id, 'btn_delivered_done', cr)
                #self.write(cr, uid, po_list_mark_done, {'state':'done'})
        except:
            raise            
        return True
    
    def _get_summary_payment_amount(self, cr, uid, ids, name, args, context=None):#Tinh Requested Amount, Paid Amount, VAT Amount theo Currency Cua Purchase
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        company_currency=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency_id=company_currency.id
        
        for po in self.browse(cr, uid, ids):
            total_request_amount=0
            total_vat_amount = 0
            subtotal_vat_amount = 0
            amount_vat = 0
            total_payment_amount=0
            
            po_currency_id = po.currency_id.id
            po_date = po.date_order
            context['date']= po_date
            total_request_amount = 0.0
            total_vat_amount = 0.0
            total_payment_amount = 0.0
            
            #po_total_amount=po.amount_total
            
            po_final_price = po.final_price
            total_request_amount_company_cur=0 #Without Tax
            
            for ksp in po.supplier_payment_ids:
                if ksp.state not in ('draft','cancel'):
                    request_amount=ksp.total
                    total_request_amount+=cur_obj.compute(cr, uid, ksp.currency_id.id, po_currency_id, request_amount, round=True, context=context)
                    #Cal total VAT Amount
                    for kspvi in ksp.kderp_vat_invoice_ids:                                               
                        total_vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, po_currency_id, kspvi.total_amount, round=True, context=context)
                        subtotal_vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, po_currency_id, kspvi.subtotal, round=True, context=context)
                        amount_vat += cur_obj.compute(cr, uid, kspvi.currency_id.id, po_currency_id, kspvi.amount_tax, round=True, context=context)
                    cal=True
                    po_final_price-=ksp.sub_total
                    exrate = ksp.exrate
                    for kp in ksp.payment_ids:
                        #if kp.state<>'draft':
                            cal=False
                            payment_amount = kp.amount
                            total_payment_amount+=cur_obj.compute(cr, uid, kp.currency_id.id, po_currency_id, payment_amount, round=True, context=context)
                            exrate = kp.exrate
                            #Sum of total payment
                    total_request_amount_company_cur+=cur_obj.round(cr, uid, company_currency, ksp.sub_total* exrate)
                    
            #Planned PO Amount in Company Currency
            total_po_amount_company_curr = total_request_amount_company_cur + cur_obj.compute(cr, uid, po.currency_id.id, company_currency.id, po_final_price, round=True, context=context)
            #Percentage of payment TotalRequestAmountINVND/(TotalRequstAMOUNT+TotalReamainAmountInVND)
            payment_percentage=total_request_amount_company_cur/total_po_amount_company_curr if total_po_amount_company_curr else 0
            #Check if payment DONE ==> Mark PO Done
            if total_request_amount==total_vat_amount and total_vat_amount==total_payment_amount and total_payment_amount==po.amount_total and po.state=='waiting_for_payment':
                result = self.write(cr, uid, [po.id], {'state':'done'})
                
            res[po.id]={'total_request_amount':total_request_amount,
                        'total_vat_amount':total_vat_amount,
                        'total_payment_amount':total_payment_amount,
                        'payment_percentage':payment_percentage,
                        'subtotal_vat_amount':subtotal_vat_amount,
                        'vat_amount':amount_vat}
        return res
    
    def _check_po_budgetover(self, cr, uid, ids, fields, arg, context={}):
        po_ids=",".join(map(str,ids))
        res={}
        cr.execute("""Select
                        po.id,
                        kbd.planned_amount,
                        planned_amount-sum(coalesce(amount,0))
                    from    
                        purchase_order po 
                    left join
                        purchase_order_line pol on po.id=order_id
                    left join
                        kderp_budget_data kbd on pol.budget_id=kbd.budget_id and pol.account_analytic_id=kbd.account_analytic_id
                    left join
                        kderp_expense_budget_line kebl on pol.budget_id=kebl.budget_id and pol.account_analytic_id=kebl.account_analytic_id and (date_order>kebl.date or (kebl.date=date_order and po.name>kebl.name))
                    where
                        po.id in (%s)
                    Group by
                        po.id,
                        pol.id,
                        kbd.id""" % (po_ids))
        for po_id in ids:
            res[po_id]  = False
            
        for po_id,bg_amount,remaining in cr.fetchall():
            if (not res[po_id] and remaining<0):
                res[po_id] = True
        return res
    
    def _get_order_from_supplier_payment(self, cr, uid, ids, context=None):
        result = {}
        ksp_obj = self.pool.get('kderp.supplier.payment')
        for ksp in ksp_obj.browse(cr, uid, ids):
            result[ksp.order_id.id]=True
        return result.keys()
    
    def _get_order_from_supplier_payment_pay(self, cr, uid, ids, context=None):
        result = {}
        kp_obj = self.pool.get('kderp.supplier.payment.pay')
        for kp in kp_obj.browse(cr, uid, ids):
            result[kp.supplier_payment_id.order_id.id]=True
        return result.keys()
    
    def _get_order_from_supplier_vat(self, cr, uid, ids, context=None):
        result = {}
        kpvi_obj = self.pool.get('kderp.supplier.vat.invoice')
        for kpvi in kpvi_obj.browse(cr, uid, ids):
            for ksp in kpvi.kderp_supplier_payment_ids:
                result[ksp.order_id.id]=True
        return result.keys()
    
    _columns={
              'total_request_amount':fields.function(_get_summary_payment_amount,string='Requested Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              'total_vat_amount':fields.function(_get_summary_payment_amount,string='Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 25),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'subtotal_vat_amount':fields.function(_get_summary_payment_amount,string='Sub-Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 30),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'vat_amount':fields.function(_get_summary_payment_amount,string='VAT Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 30),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'total_payment_amount':fields.function(_get_summary_payment_amount,string='Payment Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order'], 5),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['state','order_id'], 10),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              
              'po_final_exrate': fields.function(_get_po_final_exrate,string='PO Exrate',
                                                       method=True,type='float',digits_compute=dp.get_precision('Percent'),
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','state','discount_amount','taxes_id'], 5),
                                                              'purchase.order.line': (_get_order_from_line, None, 10),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),              
              'payment_percentage':fields.function(_get_summary_payment_amount,string='Payment Percentage',
                                                       method=True,type='float',multi="_get_summary",digits_compute=dp.get_precision('Percent'),
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','discount_amount','taxes_id'], 20),
                                                              'purchase.order.line': (_get_order_from_line, None, 10),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              'po_over':fields.function(_check_po_budgetover,string='Over',method=True,type='boolean'),
              }    
purchase_order()

class purchase_order_line(osv.osv):
    _name = "purchase.order.line"
    _inherit = 'purchase.order.line'
    _description = "KDERP Purchase Order Line"

    def _amount_in_company_curr(self, cr, uid, ids, fields, arg, context={}):
        res={}
        cur_obj=self.pool.get('res.currency')
        company_currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        
        for pol in self.browse(cr, uid, ids):
            try:
                if pol.order_id:
                    if pol.order_id.pricelist_id.currency_id.id<>company_currency_id.id:
                        res[pol.id]=pol.final_subtotal*pol.order_id.exrate*pol.order_id.po_final_exrate
                    else:
                        res[pol.id]=pol.final_subtotal*pol.order_id.exrate
                else:
                    res[pol.id]=0
            except:
                res[pol.id]=0
        return res
    
    def _get_budget(self, cr, uid, ids, fields, arg, context={}):
        pol_ids=",".join(map(str,ids))
        res={}
        cr.execute("""Select
                        pol.id,
                        kbd.planned_amount,
                        planned_amount-sum(coalesce(amount,0))
                    from    
                        purchase_order_line pol
                    left join
                        purchase_order po on order_id = po.id
                    left join
                        kderp_budget_data kbd on pol.budget_id=kbd.budget_id and pol.account_analytic_id=kbd.account_analytic_id
                    left join
                        kderp_expense_budget_line kebl on pol.budget_id=kebl.budget_id and pol.account_analytic_id=kebl.account_analytic_id and (date_order>kebl.date or (kebl.date=date_order and po.name>kebl.name))
                    where
                        pol.id in (%s)
                    Group by
                        pol.id,kbd.id""" % (pol_ids))

        for pol_id,bg_amount,remaining in cr.fetchall():
            res[pol_id]={'budget_amount':bg_amount,
                         'remaining_amount':remaining
                         }
        return res
    
    def _get_line_from_order_line(self, cr, uid, ids, context=None):
        result = {}
        for pol in self.browse(cr, uid, ids, context=context):
            for poll in pol.order_id.order_line: 
                result[poll.id] = True
        return result.keys()
    
    def _get_line_from_order(self, cr, uid, ids, context=None):
        result = {}
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for line in po.order_line: 
                result[line.id] = True
        return result.keys()
    
    def _get_order_line_from_supplier_payment(self, cr, uid, ids, context=None):
        result = {}
        ksp_obj = self.pool.get('kderp.supplier.payment')
        for ksp in ksp_obj.browse(cr, uid, ids):
            for pol in ksp.order_id.order_line:
                result[pol.id]=True
        return result.keys()
    
    def _get_order_line_from_supplier_payment_pay(self, cr, uid, ids, context=None):
        result = {}
        kp_obj = self.pool.get('kderp.supplier.payment.pay')
        for kp in kp_obj.browse(cr, uid, ids):
            for pol in kp.supplier_payment_id.order_id.order_line: 
                result[pol.id]=True
        return result.keys()
    
    _columns={
              'amount_company_curr':fields.function(_amount_in_company_curr,digits_compute=dp.get_precision('Percent'),string='Subtotal',
                                                  type='float',method=True,
                                                  store={
                                                        'purchase.order.line': (_get_line_from_order_line, ['price_unit','plan_qty'], 35),
                                                        'purchase.order': (_get_line_from_order, ['pricelist_id','date_order','state','discount_amount','po_final_exrate'], 35),
                                                        'kderp.supplier.payment': (_get_order_line_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 35),
                                                        'kderp.supplier.payment.pay': (_get_order_line_from_supplier_payment_pay, None, 35),
                                                        }),
              
              'budget_amount':fields.function(_get_budget,digits_compute=dp.get_precision('Amount'),string='Budget Amount',
                                                type='float',method=True,multi="_get_budget"),
              'remaining_amount':fields.function(_get_budget,digits_compute=dp.get_precision('Amount'),string='Remaining Amount',
                                                type='float',method=True,multi="_get_budget"),

              }
purchase_order_line()