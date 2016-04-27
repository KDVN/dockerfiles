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

class kderp_other_expense(osv.osv):
    _name = "kderp.other.expense"
    _inherit = 'kderp.other.expense'

    def _get_expense_final_exrate(self, cr, uid, ids, name, args, context=None):#Tinh PO Final Exrate khi PO Completed
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        
        company_currency=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency_id=company_currency.id
        
        for koe in self.browse(cr, uid, ids):
            if koe.currency_id.id<>company_currency_id:
                paid_amount=0
                koe_total_amount = koe.amount_total
                for kspe in koe.supplier_payment_expense_ids:
                    if kspe.state not in ('draft','cancel'):
                        cal=False
                        for kp in kspe.payment_ids:
                            #if kp.state<>'draft':
                                cal=True
                                paid_amount+=cur_obj.round(cr, uid, company_currency, kp.amount*kp.exrate)
                        if cal:
                            koe_total_amount-=kspe.total
                paid_amount+=cur_obj.compute(cr, uid, koe.currency_id.id, company_currency_id, koe_total_amount, round=True, context={'date':koe.date})
                exrate=paid_amount/(koe.amount_total*koe.exrate) if (koe.amount_total*koe.exrate) else 0
                res[koe.id]=exrate
            else:
                res[koe.id]= 1
        return res            

    def check_and_make_koe_done(self, cr, uid, ids, cron_mode=True, context=None):
        try:
            if not ids:
                ids = self.search(cr, uid, [('state','=','waiting_for_payment')])
            
            koe_list_mark_done = []
            for koe in self.browse(cr, uid, ids, context):
                if koe.state=='waiting_for_payment':
                    if koe.total_request_amount==koe.total_vat_amount and koe.total_vat_amount==koe.total_payment_amount and koe.total_payment_amount==koe.amount_total:
                        koe_list_mark_done.append(koe.id)
                else:
                    continue
                
            if koe_list_mark_done:
                self.write(cr, uid, koe_list_mark_done, {'state':'done'})
        except:
            raise            
        return True
    
    def _get_summary_payment_amount(self, cr, uid, ids, name, args, context=None):#Tinh Requested Amount, Paid Amount, VAT Amount theo Currency Cua Purchase
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        company_currency=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency_id=company_currency.id
        
        for koe in self.browse(cr, uid, ids):
            total_request_amount=0
            total_vat_amount = 0
            subtotal_vat_amount = 0
            vat_amount = 0
            total_payment_amount=0
            
            koe_currency_id = koe.currency_id.id
            koe_date = koe.date
            context['date']= koe_date
            total_request_amount = 0.0
            total_vat_amount = 0.0
            total_payment_amount = 0.0
            
            koe_subtotal_amount= koe.amount_untaxed #koe.amount_total bo
            subtotal_request_amount_company_cur=0
            total_amount = cur_obj.round(cr, uid, koe.currency_id, koe.amount_total)
            
            for kspe in koe.supplier_payment_expense_ids:
                if kspe.state not in ('draft','cancel'):
                    request_amount=kspe.total
                    total_request_amount+=cur_obj.compute(cr, uid, kspe.currency_id.id, koe_currency_id, request_amount, round=True, context=context)
                    #Cal total VAT Amount
                    for kspvi in kspe.kderp_vat_invoice_ids:
                        total_vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, koe_currency_id, kspvi.total_amount, round=True, context=context)
                        subtotal_vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, koe_currency_id, kspvi.subtotal, round=True, context=context)
                        vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, koe_currency_id, kspvi.amount_tax, round=True, context=context)
                    cal=True
                    koe_subtotal_amount-=kspe.amount
                    for kp in kspe.payment_ids:
                        #if kp.state<>'draft':
                            cal=False
                            payment_amount = kp.amount
                            total_payment_amount+=cur_obj.compute(cr, uid, kp.currency_id.id, koe_currency_id, payment_amount, round=True, context=context)
                            #Sum of total payment
                            subtotal_request_amount_company_cur+=cur_obj.round(cr, uid, company_currency, kp.amount*kp.exrate)
                    if cal:
                        subtotal_request_amount_company_cur+=cur_obj.compute(cr, uid, kspe.currency_id.id, company_currency.id, kspe.amount, round=True, context=context)
            #Planned PO Amount in Company Currency
            subtotal_koe_amount_company_curr = subtotal_request_amount_company_cur + cur_obj.compute(cr, uid, koe.currency_id.id, company_currency.id, koe_subtotal_amount, round=True, context=context)
            #Percentage of payment TotalRequestAmountINVND/(TotalRequstAMOUNT+TotalReamainAmountInVND)
            payment_percentage=subtotal_request_amount_company_cur/subtotal_koe_amount_company_curr if subtotal_koe_amount_company_curr else 0
            #Check if payment DONE ==> Mark PO Done
            if total_request_amount==total_vat_amount and total_vat_amount==total_payment_amount and total_payment_amount==total_amount and koe.state=='waiting_for_payment':
                result = self.write(cr, uid, [koe.id], {'state':'done'})
                
            res[koe.id]={'total_request_amount':total_request_amount,
                        'total_vat_amount':total_vat_amount,
                        'total_payment_amount':total_payment_amount,
                        'payment_percentage':payment_percentage,
                        'subtotal_vat_amount': subtotal_vat_amount,
                        'vat_amount':vat_amount}
        return res
    
    def _get_order_from_supplier_payment(self, cr, uid, ids, context=None):
        result = {}
        ksp_obj = self.pool.get('kderp.supplier.payment.expense')
        for kspe in ksp_obj.browse(cr, uid, ids):
            result[kspe.expense_id.id]=True
        return result.keys()
    
    def _get_expense_from_line(self, cr, uid, ids, context=None):
        result = {}
        for koel in self.pool.get('kderp.other.expense.line').browse(cr, uid, ids, context=context):
            result[koel.expense_id.id] = True
        return result.keys()
    
    def _get_order_from_supplier_payment_line(self, cr, uid, ids, context=None):
        result = {}
        kspl_obj = self.pool.get('kderp.supplier.payment.expense.line')
        for kspl in kspl_obj.browse(cr, uid, ids):
            result[kspl.supplier_payment_expense_id.expense_id.id]=True
        return result.keys()
    
    def _get_order_from_supplier_payment_pay(self, cr, uid, ids, context=None):
        result = {}
        kp_obj = self.pool.get('kderp.supplier.payment.expense.pay')
        for kp in kp_obj.browse(cr, uid, ids):
            result[kp.supplier_payment_expense_id.expense_id.id]=True
        return result.keys()
    
    def _get_order_from_supplier_vat(self, cr, uid, ids, context=None):
        result = {}
        kpvi_obj = self.pool.get('kderp.supplier.vat.invoice')
        for kpvi in kpvi_obj.browse(cr, uid, ids):
            for kspe in kpvi.kderp_supplier_payment_expense_ids:
                result[kspe.expense_id.id]=True
        return result.keys()
    
    _columns={
              'total_request_amount':fields.function(_get_summary_payment_amount,string='Requested Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date'], 20),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.expense.line':(_get_order_from_supplier_payment_line, None, 25),
                                                              'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              'total_vat_amount':fields.function(_get_summary_payment_amount,string='Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date'], 20),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','kderp_vat_invoice_ids'], 25),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'subtotal_vat_amount':fields.function(_get_summary_payment_amount,string='Subtotal Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date'], 20),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','kderp_vat_invoice_ids'], 25),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'vat_amount':fields.function(_get_summary_payment_amount,string='VAT Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date'], 20),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','kderp_vat_invoice_ids'], 25),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'total_payment_amount':fields.function(_get_summary_payment_amount,string='Payment Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date'], 5),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state'], 10),
                                                              'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              
              'exp_final_exrate': fields.function(_get_expense_final_exrate,string='Exp Exrate',
                                                       method=True,type='float',digits_compute=dp.get_precision('Percent'),
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date','state','discount_amount','taxes_id'], 5),
                                                              'kderp.other.expense.line': (_get_expense_from_line, None, 20),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.expense.line':(_get_order_from_supplier_payment_line, None, 25),
                                                              'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
                                                        
              'payment_percentage':fields.function(_get_summary_payment_amount,string='Payment Percentage',
                                                       method=True,type='float',multi="_get_summary",digits_compute=dp.get_precision('Percent'),
                                                       store={
                                                              'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','date','discount_amount','taxes_id'], 20),
                                                              'kderp.other.expense.line': (_get_expense_from_line, None, 20),
                                                              'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.expense.line':(_get_order_from_supplier_payment_line, None, 25),
                                                              'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              }    
kderp_other_expense()

class kderp_other_expense_line(osv.osv):
    _name = "kderp.other.expense.line"
    _inherit = 'kderp.other.expense.line'

    def _amount_in_company_curr(self, cr, uid, ids, fields, arg, context={}):
        res={}
        cur_obj=self.pool.get('res.currency')
        company_currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        
        for koel in self.browse(cr, uid, ids):
            try:
                if koel.expense_id.currency_id<>company_currency_id:
                    res[koel.id]=cur_obj.round(cr, uid, koel.expense_id.currency_id,koel.amount*koel.expense_id.exrate*koel.expense_id.exp_final_exrate)
                else:
                    res[koel.id]=cur_obj.round(cr, uid, koel.expense_id.currency_id,koel.amount*koel.expense_id.exrate)
            except:
                res[koel.id]=0
        return res
    
    def _get_line_from_expense_line(self, cr, uid, ids, context=None):
        result = {}
        for koel in self.browse(cr, uid, ids, context=context):
            for koell in koel.expense_id.expense_line: 
                result[koell.id] = True
        return result.keys()
        
    def _get_line_from_expense(self, cr, uid, ids, context=None):
        result = {}
        for koe in self.pool.get('kderp.other.expense').browse(cr, uid, ids, context=context):
            for line in koe.expense_line: 
                result[line.id] = True
        return result.keys()
    
    def _get_expense_line_from_supplier_payment(self, cr, uid, ids, context=None):
        result = {}
        ksp_obj = self.pool.get('kderp.supplier.payment.expense')
        for kspe in ksp_obj.browse(cr, uid, ids):
            for koel in kspe.expense_id.expense_line:
                result[koel.id]=True
        return result.keys()
    
    def _get_expense_line_from_supplier_payment_line(self, cr, uid, ids, context=None):
        result = {}
        kspel_obj = self.pool.get('kderp.supplier.payment.expense.line')
        for kspel in kspel_obj.browse(cr, uid, ids):
            for koel in kspel.supplier_payment_expense_id.expense_id.expense_line:
                result[koel.id]=True
        return result.keys()
    
    def _get_expense_line_from_supplier_payment_pay(self, cr, uid, ids, context=None):
        result = {}
        kp_obj = self.pool.get('kderp.supplier.payment.expense.pay')
        for kp in kp_obj.browse(cr, uid, ids):
            for koel in kp.supplier_payment_expense_id.expense_id.expense_line: 
                result[koel.id]=True
        return result.keys()
    
    _columns={
              'amount_company_curr':fields.function(_amount_in_company_curr,digits_compute=dp.get_precision('Budget'),string='Subtotal',
                                                  type='float',method=True,
                                                  store={
                                                        'kderp.other.expense.line': (_get_line_from_expense_line, None, 35),
                                                        'kderp.other.expense': (_get_line_from_expense, ['currency_id','date','state'], 35),
                                                        'kderp.supplier.payment.expense': (_get_expense_line_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 35),
                                                        'kderp.supplier.payment.expense.line':(_get_expense_line_from_supplier_payment_line, None, 35),
                                                        'kderp.supplier.payment.expense.pay': (_get_expense_line_from_supplier_payment_pay, None, 35),
                                                        }),
              }
kderp_other_expense_line()