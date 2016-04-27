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
#from lxml import etree
import openerp.addons.decimal_precision as dp

# from openerp import netsvc
# from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class res_company(osv.osv):
    _inherit = "res.company"
    _columns = {
        'income_currency_exchange_account_id': fields.many2one(
            'account.account',
            string="Gain Exchange Rate Account",
            domain="[('type', '=', 'other')]",),
        'expense_currency_exchange_account_id': fields.many2one(
            'account.account',
            string="Loss Exchange Rate Account",
            domain="[('type', '=', 'other')]",),
    }

res_company()

class kderp_supplier_payment_pay(osv.osv):
    _name = "kderp.supplier.payment.pay"
    _description = "KDERP Supplier Payment Pay"
    _rec_name='supplier_payment_id'

    #SYSTEM METHOD    
    def create(self, cr, uid, vals, context={}):
        new_payment_id = super(kderp_supplier_payment_pay, self).create(cr, uid, vals, context=context)
        #raise osv.except_osv('eee',new_payment_ids)
        #cr.commit()
        #new_payment_id = self._update_tax(cr, uid, new_po_ids)
        new_payment_ids=new_payment_id
        if type(new_payment_ids).__name__<>'list':
            new_payment_ids=[new_payment_ids]
        
        list_failed=[]
        ksp_ids=[]
        for kp in self.browse(cr, uid, new_payment_ids):
            if kp.supplier_payment_id.state<>'completed':
                list_failed.append(kp.supplier_payment_id.name)
            else:
                ksp_ids.append(kp.supplier_payment_id.id)
        if list_failed:
            raise osv.except_osv("KDVN Error","State of payment must be BOD Approved !\n%s" % str(list_failed))
        
        ksp_obj=self.pool.get('kderp.supplier.payment')
        for ksp_id in ksp_ids:
            ksp_obj.write(cr, uid, [ksp_id],{'state':'paid'})
            
        #result = self.action_reconcile(cr, uid, new_payment_ids, context)
        return new_payment_id
    
    def unlink(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         kspp = self.read(cr, uid, ids, ['state'], context=context)
#         unlink_ids = []
# 
#         for kp in kspp:
#             if kp['state']!='draft':
#                 raise osv.except_osv("Warning",'You cannot delete an Payment which is not draft.')
#             else:
#                 unlink_ids.append(kp['id'])

        osv.osv.unlink(self, cr, uid, ids, context=context)
        return True
    
    #For Default Value
    def _get_period(self, cr, uid, context=None):
        if context is None:
            context = {}

        periods = self.pool.get('account.period').find(cr, uid, context=context)
        return periods and periods[0] or False
    
    def _get_amount(self, cr, uid, context=None):
        if context is None:
            context= {}
        return context.get('amount', 0.0)
    
    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = self.pool.get('account.journal').search(cr, uid, [('type','=',context.get('payment_type','bank'))], limit=1)
        return res and res[0] or False
    
    _columns={
                'date':fields.date('Date', readonly=True, select=True, required=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
                'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]},domain=[('type','in',('bank','cash'))]),
                #'account_id':fields.many2one('account.account', 'Account',  states={'draft':[('readonly',False)]}),
                'period_id': fields.many2one('account.period', 'Period', readonly=True, states={'draft':[('readonly',False)]}),
                'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, required=True, states={'draft':[('readonly',False)]}),
                'amount': fields.float("Amount", digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
#                'amount_currency':fields.float("Amount Currency",digits_compute=dp.get_precision('Amount'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'exrate': fields.float("Ex.Rate",digits_compute=dp.get_precision('Amount'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
                'supplier_payment_id':fields.many2one('kderp.supplier.payment','Supplier Payment',required=True,select=True,domain="[('state','=','completed')]", readonly=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
                'move_id': fields.many2one('account.move', 'Detail', readonly=True, select=1,ondelete='restrict'),
                'writeoff':fields.boolean('Write-Off',readonly=True,states={'draft':[('readonly',False)]}),
                'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True,select=True,),
                'bank_id':fields.many2one('res.bank','Bank',readonly=True,states={'draft':[('readonly',False)]},select=True,),
              }
    _sql_constraints = [
                        ('supplier_payment_pay_unique',"unique(supplier_payment_id)","KDERP Error: The Supplier Payment must be unique !")
                        ]
    _defaults = {
        'journal_id': _get_journal,
        'writeoff': lambda *a: False,
        'state': 'draft',
        #'period_id':_get_period,
        #'date': lambda *a: time.strftime('%Y-%m-%d'),
        'exrate':lambda *a: 0.0,
        }
    
    def action_unreconcile(self, cr, uid, ids, context={}):
        obj_move_line = self.pool.get('account.move.line')
        obj_move = self.pool.get('account.move')
        ksp_obj = self.pool.get('kderp.supplier.payment')
        kp_ids=[]
        move_ids =[]
        for kp in self.browse(cr, uid, ids, context):
            move_line_ids =[]
            if kp.move_id:
                for move_line in kp.move_id.line_id:
                    move_line_ids.append(move_line.id)
#             if kp.supplier_payment_id.move_id:
#                 for move_line in kp.supplier_payment_id.move_id.line_id:
#                     move_line_ids.append(move_line.id)
                
            if move_line_ids:
                obj_move_line._remove_move_reconcile(cr, uid, move_line_ids, context=context)                    
            obj_move.button_cancel(cr, uid, [kp.move_id.id], context)
            
            self.write(cr, uid, [kp.id],{'move_id':False, 'state':'draft'}, context)
            obj_move.unlink(cr, uid, [kp.move_id.id], context)
            ksp_obj.write(cr, uid, [kp.supplier_payment_id.id], {'state':'completed'}, context)
            
        return True
    
    def action_reconcile(self, cr, uid, ids, context={}):
        if not context: context={}
                
        company=self.pool.get('res.users').browse(cr, uid, uid).company_id
        company_currency=company.currency_id
        res_obj=self.pool.get('res.currency')
        
        journal_off_ids = self.pool.get('account.journal').search(cr, uid, [('code','=','WOJ')])
        
        journal_write_off_id = journal_off_ids[0] if journal_off_ids else False
                     
        #Value will be write to Payment
        kp_vals={}
        
        for kp in self.browse(cr, uid, ids, context):
            if kp.currency_id.id<>company_currency.id:
                context['currency_id']=kp.currency_id.id
                context['amount_currency']=kp.amount
                if not kp.exrate:
                    exrate = kp.supplier_payment_id.order_id.exrate
                else:
                    exrate = kp.exrate
                #Put Period later will write to Payment
                kp_vals['exrate']=exrate                        
            else:
                exrate=kp.amount/kp.supplier_payment_id.total if kp.supplier_payment_id.total else 0
                kp_vals['exrate']=1
            #Check write off or not

            check_writeoff = kp.writeoff             
            acc_writeoff = False
            if exrate<>kp.supplier_payment_id.order_id.exrate:
                context['new_exrate'] = exrate
                if check_writeoff:
                    if exrate>kp.supplier_payment_id.exrate:
                        acc_writeoff = company.income_currency_exchange_account_id.id
                    else:
                        acc_writeoff = company.expense_currency_exchange_account_id.id
            else:
                context['new_exrate'] = False
            
            ksp_obj=self.pool.get('kderp.supplier.payment')
            
            #Check balance or not balance
            
            if context.get('new_exrate',0) and not check_writeoff:
                ksp_obj.action_cancel(cr, uid, [kp.supplier_payment_id.id], context)
                ksp_obj.action_revising_completed(cr, uid, [kp.supplier_payment_id.id], context)
                
            if kp.currency_id.id<>company_currency.id:
                new_amount = res_obj.round(cr, uid, company_currency, kp.amount*exrate)
            else:#Con lai neu la VND
                new_amount = res_obj.round(cr, uid, company_currency, kp.amount)
            #raise osv.except_osv("E",new_amount)
            #Put Period later will write to Payment
            if kp.period_id:
                pay_period_id = kp.period_id.id
            else:
                periods = self.pool.get('account.period').find(cr, uid, kp.date, context=context)
                pay_period_id = periods and periods[0] or False
                kp_vals['period_id'] = pay_period_id
            
            if kp_vals:
                context['kp_vals']=kp_vals
                
            if check_writeoff:
                move_ids = self.pay_and_reconcile(cr, uid, [kp.id], new_amount, kp.journal_id.default_credit_account_id.id, pay_period_id, kp.journal_id.id, acc_writeoff, pay_period_id, journal_write_off_id, context)
            else:
                move_ids = self.pay_and_reconcile(cr, uid, [kp.id], new_amount, kp.journal_id.default_credit_account_id.id, pay_period_id, kp.journal_id.id, False, False, False, context)
            
            #Post
            #mark_as_paid = ksp_obj.write(cr, uid, [kp.supplier_payment_id.id], {'state':'done'})
            cr.execute("""Update kderp_supplier_payment set state='done' where id = %s """ % kp.supplier_payment_id.id)
            ctx=context.copy()
            ctx['invoice'] = kp.supplier_payment_id
            
            result = self.validate_and_post(cr, uid,move_ids,context=ctx)            
        return True

    def validate_and_post(self, cr, uid, move_ids, context=None):
        move_pool = self.pool.get('account.move')
        #Validate
        for move in move_pool.browse(cr, uid, move_ids, context=context):
            # check that all accounts have the same topmost ancestor
            top_common = None
            for line in move.line_id:
                account = line.account_id
                top_account = account
                while top_account.parent_id:
                    top_account = top_account.parent_id
                if not top_common:
                    top_common = top_account
                elif top_account.id != top_common.id:
                    raise osv.except_osv(_('Error!'),
                                         _('You cannot validate this journal entry because account "%s" does not belong to chart of accounts "%s".') % (account.name, top_common.name))
        context['paid_string']='Paid for Payment No.'
        
        result=move_pool.post_supplier(cr, uid, move_ids, context=context)
        return True

    def pay_and_reconcile(self, cr, uid, ids, pay_amount, pay_account_id, period_id, pay_journal_id, writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context=None, name=''):
        if context is None:
            context = {}
        #TODO check if we can use different period for payment and the writeoff line
        assert len(ids)==1, "Can only pay one invoice at a time."
        ksp = self.browse(cr, uid, ids[0], context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        src_account_id = ksp.supplier_payment_id.account_id.id
        # Take the seq as name for move
        
        types = {'out_invoice': -1, 'in_invoice': 1, 'out_refund': 1, 'in_refund': -1}
        
        direction = types['in_invoice']
        
        date=time.strftime('%Y-%m-%d')

        # Take the amount in currency and the currency of the payment
        if 'amount_currency' in context and context['amount_currency'] and 'currency_id' in context and context['currency_id']:
            amount_currency = context['amount_currency']
            currency_id = context['currency_id']
        else:
            amount_currency = False
            currency_id = False
            
        pay_journal = self.pool.get('account.journal').read(cr, uid, pay_journal_id, ['type'], context=context)
        if pay_journal['type'] == 'bank':
            entry_type = 'bank_pay_voucher' # Bank payment
        else:
            entry_type = 'pay_voucher' # Cash payment
        
        ref = ksp.supplier_payment_id.name
        
        partner = self.pool['res.partner']._find_accounting_partner(ksp.supplier_payment_id.order_id.partner_id)
        # Pay attention to the sign for both debit/credit AND amount_currency
        l1 = {
            'debit': direction * pay_amount>0 and direction * pay_amount,
            'credit': direction * pay_amount<0 and - direction * pay_amount,
            'account_id': src_account_id,
            'partner_id': partner.id,
            'ref':ref,
            'date': date,
            'currency_id':currency_id,
            'amount_currency':amount_currency and direction * amount_currency or 0.0,
            'company_id': company.id,
        }
        l2 = {
            'debit': direction * pay_amount<0 and - direction * pay_amount,
            'credit': direction * pay_amount>0 and direction * pay_amount,
            'account_id': pay_account_id,
            'partner_id': partner.id,
            'ref':ref,
            'date': date,
            'currency_id':currency_id,
            'amount_currency':amount_currency and - direction * amount_currency or 0.0,
            'company_id': company.id,
        }

        if not name:
            name = ksp.supplier_payment_id.name
        l1['name'] = name
        l2['name'] = name

        lines = [(0, 0, l1), (0, 0, l2)]
        move = {'ref': ref, 'line_id': lines, 'journal_id': pay_journal_id, 'period_id': period_id, 'date': date}

        move_id = self.pool.get('account.move').create(cr, uid, move, context=context)
        
        line_ids = []
        total = 0.0
        line = self.pool.get('account.move.line')
        move_ids = [move_id,]
        if ksp.supplier_payment_id.move_id:
            move_ids.append(ksp.supplier_payment_id.move_id.id)
        
        cr.execute('SELECT id FROM account_move_line '\
                   'WHERE move_id IN %s',
                   ((move_id, ksp.supplier_payment_id.move_id.id),))
        lines = line.browse(cr, uid, map(lambda x: x[0], cr.fetchall()))
        for l in lines:#+ ksp.supplier_payment_id.payment_ids
            if l.account_id.id == src_account_id:
                line_ids.append(l.id)
                total += (l.debit or 0.0) - (l.credit or 0.0)

        inv_id, name = self.name_get(cr, uid, [ksp.id], context=context)[0]
        
        self.pool.get('account.move.line').reconcile(cr, uid, line_ids, 'auto', writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context)
      
        # Update the stored value (fields.function), so we write to trigger recompute
        kp_vals=context.get('kp_vals',{})
        kp_vals['state']='done'
        kp_vals['move_id']=move_id
        
        self.write(cr, uid, ids, kp_vals, context=context)
        
        return move_ids
    
    def load(self, cr, uid, fields, data, context=None):
    #def import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
        try:
            payment_id_pos = fields.index('supplier_payment_id')
        except:
            payment_id_pos = -1
        
        fields_list_need=['amount','currency_id','exrate']
        list_remove = set(fields).intersection(set(fields_list_need)) #Tra ve cac truong da co trong file import
        
        list_to_get=list(set(fields_list_need)-list_remove)
        
        list_field_to_import=fields
        list_field_to_import.extend(list_to_get)
        #raise osv.except_osv("E",data)
        payment_no_list =[]
        if payment_id_pos>=0:
            new_data={}
            for pos in range(len(data)):
                payment_no_list.append(str(data[pos][payment_id_pos]))
                new_data.update({str(data[pos][payment_id_pos]):data[pos]})
            payment_nos =str(payment_no_list).replace("[","(").replace("]",")") #",".join(map(str,payment_no_list))
#             raise osv.except_osv("KDVN Error",new_data)
            cr.execute("Select name from kderp_supplier_payment krop where name in %s and state!='completed'" % (payment_nos))
            if cr.rowcount>0:
                 list1 =[]
                 for pn in cr.fetchall():
                     list1.append(str(pn[0]))
                 raise osv.except_osv("KDVN Error","State of payment must be BOD Approved !\n%s" % str(list1))
            else:
                if list_to_get:
                    list_field_str=str(list_to_get).replace("[","").replace("]","").replace("'","").replace('currency_id', "'''' || rc.name || ''''").replace('amount','total')
                    cr.execute("Select krop.name,(%s) from kderp_supplier_payment krop left join res_currency rc on currency_id=rc.id where krop.name in %s and state='completed'" % (list_field_str,payment_nos))
                    for key,value in cr.fetchall():
                        if type(value)==type(""):
                            value=eval(value)                        
                        new_data[key]=new_data[key]+value
                    new_data2=[]
                    for x in new_data:
                        new_data2.append(new_data[x])
                    if new_data2:
                        data=new_data2
        
        return super(kderp_supplier_payment_pay, self).load( cr, uid, list_field_to_import, data, context)
kderp_supplier_payment_pay()

class kderp_supplier_payment(osv.osv):
    _name = 'kderp.supplier.payment'
    _inherit = 'kderp.supplier.payment'
            
    _columns={
                'payment_ids':fields.one2many('kderp.supplier.payment.pay','supplier_payment_id','Payment', required=True, readonly=True, states={'draft':[('readonly',False)],'completed':[('readonly',False)],'revising':[('readonly',False)]})
             }
    
kderp_supplier_payment()