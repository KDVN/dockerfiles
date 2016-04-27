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

class kderp_received(osv.osv):
    _name = "kderp.received"
    _description = "KDERP Received"
    _rec_name='client_payment_id'

    #SYSTEM METHOD    
    def create(self, cr, uid, vals, context={}):
        new_payment_id = super(kderp_received, self).create(cr, uid, vals, context=context)
        new_payment_ids=new_payment_id
        if type(new_payment_ids).__name__<>'list':
            new_payment_ids=[new_payment_ids]
        
        list_failed=[]
        for kr in self.browse(cr, uid, new_payment_ids):
            if kr.client_payment_id.state<>'open':
                list_failed.append(kr.client_payment_id.number)
                
        if list_failed:
            raise osv.except_osv("KDVN Error","State of Client Payment must be Waiting for Payment !\n%s" % str(list_failed))
        result = self.action_reconcile(cr, uid, new_payment_ids, context)
        return new_payment_id
        
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        kr_list = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for kr in kr_list:
            if kr['state']=='draft' or not kr['state']:
                unlink_ids.append(kr['id'])
            else:
                raise osv.except_osv("Warning",'You cannot delete an Payment which is not draft.')

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
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
        return context.get('amount', 0.0)*context.get('exrate', 0.0)
    
    def _get_currency_id(self, cr, uid, context=None):
        if context is None:
            context= {}
        curr_id= self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        return curr_id    
    
    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = self.pool.get('account.journal').search(cr, uid, [('type','=',context.get('payment_type','bank'))], limit=1)
        return res and res[0] or False
    
    _columns={
                'date':fields.date('Date', readonly=True,required=True, select=True, states={'draft':[('readonly',False)]}),
                'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]},domain=[('type','in',('bank','cash'))]),
                'period_id': fields.many2one('account.period', 'Period', readonly=True, states={'draft':[('readonly',False)]}),
                'currency_id': fields.many2one('res.currency', 'Currency', readonly=True, required=True, states={'draft':[('readonly',False)]}),
                'amount': fields.float("Amount", digits_compute=dp.get_precision('Account'), required=True),
                'exrate': fields.float("Ex.Rate",digits_compute=dp.get_precision('Amount'), required=True),
                'client_payment_id':fields.many2one('account.invoice','Client Payment',select=1,required=True, readonly=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
                'move_id': fields.many2one('account.move', 'Detail', readonly=True, select=1,ondelete='restrict'),
                'writeoff':fields.boolean('Write-Off',readonly=True,states={'draft':[('readonly',False)]}),
                'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True),
                'bank_id':fields.many2one('res.partner.bank','Bank',readonly=True,states={'draft':[('readonly',False)]}),
              }
    _defaults = {
        'journal_id': _get_journal,
        'writeoff': lambda *a: False,
        'state': 'draft',
        'exrate':1.0,
        'amount':_get_amount,
        'currency_id':_get_currency_id
        }
    
    def open_received(self, cr, uid, ids, context=None):
        if not context:
            context={}
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Received Money',
            'view_type': 'form',
            'res_id':ids[0],
            'target':'current',
            'nodestroy': True,
            'view_mode': 'form,tree',
            'res_model': 'kderp.received',
            'domain': "[('id','in',%s)]" % ids
            }
        
    def action_unreconcile(self, cr, uid, ids, context={}):
        obj_move_line = self.pool.get('account.move.line')
        obj_move = self.pool.get('account.move')
        kcp_obj = self.pool.get('account.invoice')
        kp_ids=[]
        move_ids =[]
        for kr in self.browse(cr, uid, ids, context):
            move_line_ids =[]
            if kr.move_id:
                for move_line in kr.move_id.line_id:
                    move_line_ids.append(move_line.id)

            if move_line_ids:
                obj_move_line._remove_move_reconcile(cr, uid, move_line_ids, context=context)                    
            obj_move.button_cancel(cr, uid, [kr.move_id.id], context)
            
            self.write(cr, uid, [kr.id],{'move_id':False, 'state':'draft'}, context)
            obj_move.unlink(cr, uid, [kr.move_id.id], context)

            kcp_obj.action_cancel_draft(cr, uid, [kr.client_payment_id.id], context)
            
        return {'type': 'ir.actions.client',
                'tag': 'reload'}
    
    def action_reconcile(self, cr, uid, ids, context={}):
        if not context: context={}
                
        company=self.pool.get('res.users').browse(cr, uid, uid).company_id
        company_currency=company.currency_id
        res_obj=self.pool.get('res.currency')
        
        journal_off_ids = self.pool.get('account.journal').search(cr, uid, [('code','=','WOJ')])
        
        journal_write_off_id = journal_off_ids[0] if journal_off_ids else False
                     
        #Value will be write to Payment
        kr_vals={}
        kcp_obj=self.pool.get('account.invoice')
        for kr in self.browse(cr, uid, ids, context):
            if kr.currency_id.id<>company_currency.id:
                context['currency_id']=kr.currency_id.id
                context['amount_currency']=kr.amount
                if not kr.exrate:
                    exrate = kr.client_payment_id.exrate
                else:
                    exrate = kr.exrate
                    
                #Put Period later will write to Payment
                #kr_vals['exrate']=exrate
            elif kr.currency_id.id<>kr.client_payment_id.currency_id:
                exrate=(kr.amount/kr.client_payment_id.amount_total) if kr.client_payment_id.amount_total else 0 
                #kr_vals['exrate']=exrate
            else:
                exrate=1
                #kr_vals['exrate']=1
            #Check write off or not

            check_writeoff = kr.writeoff             
            acc_writeoff = False
            if check_writeoff:
                    acc_writeoff = company.income_currency_exchange_account_id.id
                    context['comment']='Write-Off for %s' % kr.client_payment_id.number
            if exrate<>kr.client_payment_id.exrate:
                context['new_exrate'] = exrate                                    
            else:                
                context['new_exrate'] = 0

            #Check balance or not balance
            
            #if  :
             #   kcp_obj.write(cr, uid, kr.client_payment_id.id, {'exrate':context.get('new_exrate',0)})
            
            if not check_writeoff and context.get('new_exrate',0) and kr.client_payment_id.currency_id.id<>company_currency.id:
                #kcp_obj.write(cr, uid, kr.client_payment_id.id, {'exrate':context['new_exrate']},context)
                context['exrate']=context['new_exrate']
                kcp_obj.action_cancel(cr, uid, [kr.client_payment_id.id], context)
                context['ignore_check_reconcile']=True
                kcp_obj.btn_action_revising_completed(cr, uid, [kr.client_payment_id.id], context)
            
            if kr.currency_id.id<>company_currency.id:
                new_amount = res_obj.round(cr, uid, company_currency, kr.amount*exrate)
            else:#Con lai neu la VND
                new_amount = res_obj.round(cr, uid, company_currency, kr.amount)
            #raise osv.except_osv("E",new_amount)
            #Put Period later will write to Payment
            if kr.period_id:
                receive_period_id = kr.period_id.id
            else:
                periods = self.pool.get('account.period').find(cr, uid, kr.date, context=context)
                receive_period_id = periods and periods[0] or False
                kr_vals['period_id'] = receive_period_id
            
            if kr_vals:
                context['kr_vals']=kr_vals
            
            if check_writeoff:
                move_ids = self.pay_and_reconcile(cr, uid, [kr.id], new_amount, kr.journal_id.default_credit_account_id.id, receive_period_id, kr.journal_id.id, acc_writeoff, receive_period_id, journal_write_off_id, context)
            else:
                move_ids = self.pay_and_reconcile(cr, uid, [kr.id], new_amount, kr.journal_id.default_credit_account_id.id, receive_period_id, kr.journal_id.id, False, False, False, context)
            
            #Post
            mark_as_paid = kcp_obj.write(cr, uid, [kr.client_payment_id.id], {'state':'paid'})
            ctx=context.copy()
            ctx['invoice'] = kr.client_payment_id
            
            result = self.validate_and_post(cr, uid,move_ids,context=ctx)
 
#             wf_service = netsvc.LocalService("workflow")
#             try:
#                 wf_service.trg_delete(uid, 'account.invoice', kr.client_payment_id.id, cr)
#             except:
#                 continue
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
        context['paid_string']='Collect for Payment No.'
        
        result=move_pool.post(cr, uid, move_ids, context=context)
        
        return True

    def pay_and_reconcile(self, cr, uid, ids, pay_amount, pay_account_id, period_id, pay_journal_id, writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context=None, name=''):
        if context is None:
            context = {}
        #TODO check if we can use different period for payment and the writeoff line
        assert len(ids)==1, "Can only pay one invoice at a time."
        kr = self.browse(cr, uid, ids[0], context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        src_account_id = kr.client_payment_id.account_id.id
        # Take the seq as name for move
        
        types = {'out_invoice': -1, 'in_invoice': 1, 'out_refund': 1, 'in_refund': -1}
        
        direction = types['out_invoice']
        
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
        
        ref = kr.client_payment_id.name
        
        partner = self.pool['res.partner']._find_accounting_partner(kr.client_payment_id.partner_id)
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
            name = kr.client_payment_id.name
        l1['name'] = name
        l2['name'] = name

        lines = [(0, 0, l1), (0, 0, l2)]
        
        move = {'ref': ref, 'line_id': lines, 'journal_id': pay_journal_id, 'period_id': period_id, 'date': date}
        
        move_id = self.pool.get('account.move').create(cr, uid, move, context=context)
        
        line_ids = []
        total = 0.0
        line = self.pool.get('account.move.line')
        move_ids = [move_id,]
        if kr.client_payment_id.move_id:
            move_ids.append(kr.client_payment_id.move_id.id)
        
        cr.execute('SELECT id FROM account_move_line '\
                   'WHERE move_id IN %s',
                   ((move_id, kr.client_payment_id.move_id.id),))
        lines = line.browse(cr, uid, map(lambda x: x[0], cr.fetchall()))
        for l in lines:#+ kr.client_payment_id.payment_ids
            if l.account_id.id == src_account_id:
                line_ids.append(l.id)
                total += (l.debit or 0.0) - (l.credit or 0.0)

        inv_id, name = self.name_get(cr, uid, [kr.id], context=context)[0]

        self.pool.get('account.move.line').reconcile(cr, uid, line_ids, 'auto', writeoff_acc_id, writeoff_period_id, writeoff_journal_id, context)
      
        # Update the stored value (fields.function), so we write to trigger recompute
        kr_vals=context.get('kr_vals',{})
        kr_vals['state']='done'
        kr_vals['move_id']=move_id
        
        self.write(cr, uid, ids, kr_vals, context=context)
        
        return move_ids
    
kderp_received()

class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
        
    def _get_payment_date(self, cr, uid, ids, name, args, context=None):
        res={}
        for ai in self.browse(cr, uid, ids):
            Date = None
            for kr in ai.received_ids:
                Date=kr.date
            res[ai.id] = Date
        return res
    
    def _get_invoice_from_received(self, cr, uid, ids, context=None):
        result = {}
        for kr in self.pool.get('kderp.received').browse(cr, uid, ids, context=context):
            result[kr.client_payment_id.id] = True
        return result.keys()
    
    _columns={
                'received_ids':fields.one2many('kderp.received','client_payment_id','Payment', readonly=True, required=True, states={'draft':[('readonly',False)],'open':[('readonly',False)]}),
                'payment_date':fields.function(_get_payment_date,type='date',method=True,string='Payment Date',
                                               store={
                                                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['state'], 20),
                                                        'kderp.received': (_get_invoice_from_received, None, 20)})
             }
    
account_invoice()