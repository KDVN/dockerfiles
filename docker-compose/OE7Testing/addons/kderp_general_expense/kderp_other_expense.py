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
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)                       
            if not ids:
                ids = self.search(cr, user, [('account_analytic_id',operator,name)]+ args, limit=limit, context=context)    
            if not ids:
                ids = self.search(cr, user, [('description', operator, name)]+ args, limit=limit, context=context)            
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            if record.description and context.get('general_expense', False):
                full_name = '%s - %s' % (record.name,record.description)
            else:
                full_name = record.name
            res.append((record.id, full_name))
        return res
    
    def check_and_make_koe_done(self, cr, uid, ids, cron_mode=True, context=None):                
        try:
            if not ids:
                ids = self.search(cr, uid, [('state','in',('waiting_for_payment','paid'))])
            
            koe_list_mark_done = []
            koe_list_mark_done_remain = []
            koe_list_mark_paid = []
            check_ot_ids = []
            
            for koe in self.browse(cr, uid, ids, context):
                if koe.expense_type == 'monthly_expense' and koe.state not in ('draft','cancel'):                    
                    koe_list_mark_done.append(koe.id)
                    for koel in koe.expense_line:
                        if koel.belong_expense_id:
                            if koel.belong_expense_id.state in ('paid'):
                                check_ot_ids.append(koel.belong_expense_id.id)                                            
                else:
                    check_type = koe.expense_type not in ('prepaid','fixed_asset')
                    check_state =  koe.state in ('waiting_for_payment','revising')              
                    check_amount = koe.total_request_amount==koe.total_vat_amount and koe.total_vat_amount==koe.total_payment_amount and koe.total_payment_amount==koe.amount_total 
                    if check_type and check_state and check_amount:
                        koe_list_mark_done.append(koe.id)
                    elif not check_type and (check_state or koe.state=='paid') and check_amount:
                        check_amount_remain = (koe.remaining_amount == 0 and koe.total_request_amount>0)
                        if (not check_amount_remain and koe.state!='paid'):
                            koe_list_mark_paid.append(koe.id)
                        elif check_amount_remain and koe.state in ('paid','revising'):                        
                            koe_list_mark_done_remain.append(koe.id)                            
                    else:
                        continue
                      
            if koe_list_mark_done:
                #self.write(cr, uid, koe_list_mark_done, {'state':'done'})
                cr.execute("""Update kderp_other_expense set state='done' where id in (%s) """ % ",".join(map(str, koe_list_mark_done)))                
            if koe_list_mark_paid:
                #self.write(cr, uid, koe_list_mark_paid, {'state':'paid'})
                cr.execute("""Update kderp_other_expense set state='paid' where id in (%s) """ % ",".join(map(str, koe_list_mark_paid)))
            if koe_list_mark_done_remain:
                cr.execute("""Update kderp_other_expense set state='done' where id in (%s) """ % ",".join(map(str, koe_list_mark_done_remain)))
            if check_ot_ids:
                self.check_and_make_koe_done(cr, uid, check_ot_ids, context=context)
        except:
            raise            
        return True    
    
    def action_revising_done(self, cr, uid, ids, context=None):
        return self.check_and_make_koe_done(cr, uid, ids, context)
    
    def action_done_revising(self, cr, uid, ids, context=None):
        if ids:              
            cr.execute("""Update kderp_other_expense set state='revising' where id in (%s) """ % ",".join(map(str, ids)))
        return ids
    
    def _get_expense_final_exrate(self, cr, uid, ids, name, args, context=None):#Tinh PO Final Exrate khi PO Completed
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        
        company_currency = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency_id=company_currency.id
        
        for koe in self.browse(cr, uid, ids):
            if koe.currency_id.id<>company_currency_id and koe.expense_type <> 'monthly_expense':
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
                paid_amount +=  cur_obj.round(cr, uid, company_currency, koe.exrate * koe_total_amount)
                exrate= paid_amount/(koe.amount_total*koe.exrate) if (koe.amount_total*koe.exrate) else 0
                res[koe.id] = exrate
            else:
                res[koe.id]= 1
        return res    
    
    def _get_summary_payment_amount(self, cr, uid, ids, name, args, context=None):#Tinh Requested Amount, Paid Amount, VAT Amount theo Currency Cua Purchase
        #Not yet move vat_amount received from kderp_payment Please add move vat_amount if using it ########################NOTICE###########################
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        company_currency = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
                
        for koe in self.browse(cr, uid, ids):            
            
            koe_currency_id = koe.currency_id.id
            koe_currency = koe.currency_id
            koe_date = koe.date
            context['date']= koe_date
            total_request_amount = 0.0
            total_vat_amount = 0.0
            subtotal_vat_amount = 0
            total_payment_amount = 0.0
            
            koe_subtotal_amount = koe.amount_untaxed #koe.amount_total bo
            subtotal_request_amount_company_cur = 0
            if koe.expense_type == 'monthly_expense':
                if koe.state not in ('draft','cancel'):
                    total_request_amount = koe.amount_total
                    total_payment_amount = total_request_amount
                    total_vat_amount = total_payment_amount
                    subtotal_vat_amount = koe.amount_untaxed
                    payment_percentage = 1
                else:
                    total_request_amount = 0
                    total_payment_amount = 0
                    total_vat_amount = 0
                    subtotal_vat_amount = 0
                    payment_percentage = 1
            else:
                for kspe in koe.supplier_payment_expense_ids:
                    if kspe.state not in ('draft','cancel'):
                        request_amount = kspe.total
                        #In case payment is VND and Other Expense in Other Currency
                        if company_currency.id == kspe.currency_id.id and koe_currency_id!=company_currency.id:
                            total_request_amount += cur_obj.round(cr, uid, koe.currency_id, koe.exrate*request_amount)
                        else:
                            total_request_amount += cur_obj.compute(cr, uid, kspe.currency_id.id, koe_currency_id, request_amount, round=True, context=context)
                        #Cal total VAT Amount
                        for kspvi in kspe.kderp_vat_invoice_ids:
                            vat_amount=kspvi.total_amount
                            vat_subtotal=kspvi.subtotal
                            if company_currency.id == kspvi.currency_id.id and koe_currency_id!=company_currency.id:
                                #Incase vat invoice same currency with Company Currency and Expense not
                                if koe.exrate:
                                    total_vat_amount += cur_obj.round(cr, uid, koe.currency_id, vat_amount/koe.exrate)
                                    subtotal_vat_amount += cur_obj.round(cr, uid, koe.currency_id, vat_subtotal/koe.exrate)
                            else: 
                                total_vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, koe_currency_id, vat_amount, round=True, context=context)
                                subtotal_vat_amount += cur_obj.compute(cr, uid, kspvi.currency_id.id, koe_currency_id, vat_subtotal, round=True, context=context)
                        cal=True
                        koe_subtotal_amount -= kspe.amount
                        for kp in kspe.payment_ids:
                            #if kp.state<>'draft':
                                cal=False
                                payment_amount = kp.amount
                                if company_currency.id == kp.currency_id.id and koe_currency_id!=company_currency.id:
                                    total_payment_amount += cur_obj.round(cr, uid, koe_currency, payment_amount * koe.exrate)
                                else:
                                    total_payment_amount += cur_obj.compute(cr, uid, kp.currency_id.id, koe_currency_id, payment_amount, round=True, context=context)
                                #Sum of total payment
                                subtotal_request_amount_company_cur += cur_obj.round(cr, uid, company_currency, kp.amount*kp.exrate)
                        if cal:
                            subtotal_request_amount_company_cur += cur_obj.compute(cr, uid, kspe.currency_id.id, company_currency.id, kspe.amount, round=True, context=context)
                #Planned PO Amount in Company Currency
                subtotal_koe_amount_company_curr = subtotal_request_amount_company_cur + cur_obj.compute(cr, uid, koe.currency_id.id, company_currency.id, koe_subtotal_amount, round=True, context=context)
                #Percentage of payment TotalRequestAmountINVND/(TotalRequstAMOUNT+TotalReamainAmountInVND)
                payment_percentage = subtotal_request_amount_company_cur/subtotal_koe_amount_company_curr if subtotal_koe_amount_company_curr else 0
            #Check if payment DONE ==> Mark PO Done
#             check_type = koe.expense_type not in ('prepaid','fixed_asset') 
#             check_state =  koe.state=='waiting_for_payment'
#             check_amount = total_request_amount == total_vat_amount and total_vat_amount == total_payment_amount and total_payment_amount==koe.amount_total
#             not_monthly_expense = koe.expense_type != 'monthly_expense'
#             if check_amount and check_state and check_type and not_monthly_expense:
#                 result = self.write(cr, uid, [koe.id], {'state':'done'})
#             elif  check_amount and not check_state and check_type and not_monthly_expense:
#                 result = self.write(cr, uid, [koe.id], {'state':'paid'})
                
            res[koe.id]={'total_request_amount':total_request_amount,
                        'total_vat_amount':total_vat_amount,
                        'total_payment_amount':total_payment_amount,
                        'payment_percentage':payment_percentage,
                        'subtotal_vat_amount':subtotal_vat_amount}
        self.check_and_make_koe_done(cr, uid, ids, context)
        return res
    
    def _get_exrate(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        company_currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        res = {}        
        for exp in self.browse(cr,uid,ids):
            exrate = exp.manual_exrate if exp.manual_exrate else cur_obj.compute(cr, uid, exp.currency_id.id, company_currency_id, 1, round=False,context={'date': exp.date})                
            res[exp.id]= exrate        
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
              
            'manual_exrate':fields.float('Manual Exrate.'),
            
            'exrate':fields.function(_get_exrate,help='Exchange rate from currency to company currency',
                                         method=True,string="Ex.Rate",type='float',digits_compute=dp.get_precision('Amount')),
              
            'total_request_amount':fields.function(_get_summary_payment_amount,string='Requested Amt.',
                                                     method=True,type='float',multi="_get_summary",
                                                     store={
                                                            'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['manual_exrate','currency_id','date','expense_type','state'], 20),
                                                            'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 25),
                                                            'kderp.supplier.payment.expense.line':(_get_order_from_supplier_payment_line, None, 25),
                                                            'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                           }),
            'subtotal_vat_amount':fields.function(_get_summary_payment_amount,string='SubStotal Recei. Amt.',
                                                     method=True,type='float',multi="_get_summary",
                                                     store={
                                                            'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['manual_exrate','currency_id','date','expense_type','state'], 20),
                                                            'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','kderp_vat_invoice_ids'], 25),
                                                            'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                           }),            
            'total_vat_amount':fields.function(_get_summary_payment_amount,string='Total Invoice Amt.',
                                                     method=True,type='float',multi="_get_summary",
                                                     store={
                                                            'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['manual_exrate','currency_id','date','expense_type','state'], 20),
                                                            'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','kderp_vat_invoice_ids'], 25),
                                                            'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                           }),
            'total_payment_amount':fields.function(_get_summary_payment_amount,string='Payment Amt.',
                                                     method=True,type='float',multi="_get_summary",
                                                     store={
                                                            'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['manual_exrate','currency_id','date','expense_type','state'], 5),
                                                            'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state'], 10),
                                                            'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                           }),
               
            'exp_final_exrate': fields.function(_get_expense_final_exrate,string='Exp Exrate',
                                                     method=True,type='float',digits_compute=dp.get_precision('Percent'),
                                                     store={
                                                            'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['manual_exrate','currency_id','date','state','taxes_id','expense_type'], 5),
                                                            'kderp.other.expense.line': (_get_expense_from_line, None, 20),
                                                            'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 25),
                                                            'kderp.supplier.payment.expense.line':(_get_order_from_supplier_payment_line, None, 25),
                                                            'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                           }),
                                                         
            'payment_percentage':fields.function(_get_summary_payment_amount,string='Payment Percentage',
                                                     method=True,type='float',multi="_get_summary",digits_compute=dp.get_precision('Percent'),
                                                     store={
                                                            'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['manual_exrate','currency_id','date','discount_amount','taxes_id','expense_type','state'], 20),
                                                            'kderp.other.expense.line': (_get_expense_from_line, None, 20),
                                                            'kderp.supplier.payment.expense': (_get_order_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 25),
                                                            'kderp.supplier.payment.expense.line':(_get_order_from_supplier_payment_line, None, 25),
                                                            'kderp.supplier.payment.expense.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                           }),
              }

    def _check_manual_vat(self, cr, uid, ids):
        koe_ids = {}
        self.pool.get('ir.rule').clear_cache(cr,uid)
        for koe in self.browse(cr, uid, ids):
            for koel in koe.expense_line:
                if koel.manual_vat:
                    koe_ids[koe.id] = True
        koe_taxes = self._amount_all(cr, uid, koe_ids.keys(),['amount_tax'], {}, {})
        for koe in self.browse(cr, uid, koe_ids.keys()):
            subtotalVATAmount = 0
            for koel in koe.expense_line:
                subtotalVATAmount += koel.manual_vat
            amountTAXOE = koe_taxes[koe.id]['amount_tax']
            if amountTAXOE <> subtotalVATAmount:
                raise osv.except_osv("KDERP Warning", "Please check VAT Amount")
        return True

    _constraints = [(_check_manual_vat, "",['taxes_id','expense_line'])]
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
                                                        'kderp.other.expense': (_get_line_from_expense, ['manual_exrate','currency_id','date','discount_amount','taxes_id','expense_type','state'], 35),
                                                        'kderp.supplier.payment.expense': (_get_expense_line_from_supplier_payment, ['expense_id','state','amount','taxes_id','currency_id','date'], 35),
                                                        'kderp.supplier.payment.expense.line':(_get_expense_line_from_supplier_payment_line, None, 35),
                                                        'kderp.supplier.payment.expense.pay': (_get_expense_line_from_supplier_payment_pay, None, 35),
                                                        }),
              'manual_vat': fields.float("Manual VAT", digits = (16,2))
              }
    #
    # def _check_manual_vat(self, cr, uid, ids):
    #     koe_ids = {}
    #     for koel in self.browse(cr, uid, ids):
    #         if koel.manual_vat:
    #             koe_ids[koel.expense_id.id] = True
    #     oe_keys = self.pool.get('kderp.other.expense')._amount_all(cr, uid, koe_ids.keys(), 'amount_tax', {}, context={})
    #
    #     import pdb
    #     pdb.set_trace()
    #     for koe in self.pool.get('kderp.other.expense').browse(cr, uid, koe_ids.keys()):
    #         subtotalVATAmount = 0
    #         for koel in koe.expense_line:
    #             subtotalVATAmount += koel.manual_vat
    #         amountTAXOE = oe_keys[koe.id]['amount_tax']
    #         if amountTAXOE <> subtotalVATAmount:
    #             raise osv.except_osv("KDERP Warning", "Please check VAT Amount")
    #     return True
    #
    # _constraints = [(_check_manual_vat, "",['manual_vat','expense_id'])]
kderp_other_expense_line()