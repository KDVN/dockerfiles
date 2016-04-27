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

import time
from lxml import etree
import openerp.addons.decimal_precision as dp

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

class account_tax(osv.osv):
    _inherit='account.tax'
    _name = 'account.tax'
    _description = 'Tax'
    
    def compute_all(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False):
        """
        :param force_excluded: boolean used to say that we don't want to consider the value of field price_include of
            tax. It's used in encoding by line where you don't matter if you encoded a tax with that boolean to True or
            False
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Amount')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = float_round(price_unit * quantity, precision)
        tin = []
        tex = []
        for tax in taxes:
            if not tax.price_include or force_excluded:
                tex.append(tax)
            else:
                tin.append(tax)
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        totlex_qty = 0.0
        try:
            totlex_qty = totalex/quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex
        }

account_tax()

class account_invoice_tax(osv.osv):
    _name = "account.invoice.tax"
    _inherit = "account.invoice.tax"
    _description = "Invoice Tax"
       
#Thay doi cach tinh ti gia
    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        inv_cur=inv.currency_id
        company_currency = inv.company_id.currency_id.id
        if not context:
            context={}
            
        context = {'date': inv.date_invoice or time.strftime('%Y-%m-%d'),
                 'invoice_id':inv.id}

        for line in inv.invoice_line:
            if inv.tax_base=='p':
                compute_amount=line.amount
            elif inv.tax_base=='p_adv':
                compute_amount=line.advanced
            elif inv.tax_base=='p_retention':
                compute_amount=line.retention
            else:
                compute_amount=line.price_unit
                
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, compute_amount, line.quantity, line.product_id, inv.partner_id)['taxes']:
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'] * line['quantity'])
                
                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context=context, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context=context, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context=context, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context=context, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, inv_cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, inv_cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped       
       
    def _get_acc(self, cr, uid, context=None):
        if context is None:
            context = {}
        acc_obj=self.pool.get('account.account')
        acc_id =acc_obj.search(cr,uid,[('code','=','333110')])
        if acc_id:
            acc_id = acc_id[0]
        else:
            acc_id = False 
        return acc_id
    
    _columns={
              'account_id': fields.many2one('account.account', 'Tax Account', required=True, domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')]),
              #'tax_id':fields.many2one('account.tax','VAT',required=True)
              }
    _defaults={
               'account_id':_get_acc
               }
account_invoice_tax()

class account_invoice(osv.osv):
    
    _name = "account.invoice"
    _inherit = ['mail.thread','account.invoice']
    _description = 'Client Payment'
    _order = "number desc,id asc"
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        unlink_ids = []
        for ai in self.browse(cr, uid, ids):
            if ai.state not in ('draft', 'cancel'):
                raise osv.except_osv(_('KDERP Warning'),_('You cannot delete an Client Payment which is not draft or cancelled'))
#             elif ai.invoice_line:
#                 raise osv.except_osv(_('KDERP Warning'),_('You cannot delete an Client Payment which have Job in details'))
            else:
                unlink_ids.append(ai.id)
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        return [(r['id'], '%s' % (r['number'] or 'Not Avaible')) for r in self.read(cr, uid, ids, ['number'], context, load='_classic_write')]
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('number','=',name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('number',operator,name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('invoice_line',operator,name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name',operator,name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if not context:
            context={}
        #Open Client Payment from Quotation
        quo_ids = context.get("kderp_search_default_quotation_from_payment_lists",[])
        if quo_ids:
            payment_ids=[]
            for so in self.pool.get('sale.order').browse(cr, uid, quo_ids):
                if so.contract_id:
                   for kcp in so.contract_id.client_payment_ids:
                        payment_ids.append(kcp.id)
            args.append((('id', 'in', payment_ids)))
        
        #Open Client Payment from JOB    
        job_ids = context.get("kderp_search_default_job_payment_client_lists",[])
        if job_ids:
            payment_ids=[]
            for job in self.pool.get('account.analytic.account').browse(cr, uid, job_ids):
               for kcc in job.contract_ids:
                   for kcp in kcc.client_payment_ids:
                       payment_ids.append(kcp.id)
            args.append((('id', 'in', payment_ids)))
        return super(account_invoice, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)
 
    def action_move_create(self, cr, uid, ids, context=None):
        if not context:
            context={}
        for inv in self.browse(cr, uid, ids, context=context):
            #if inv.exrate<=0:
            #    raise osv.except_osv(_('KDERP Error!'), _('Please Input Ex.Rate for this payment.'))
            context.update({'invoice_id':inv.id})
        
        r = self.button_reset_taxes(cr, uid, ids, context)
        
        result = super(account_invoice, self).action_move_create(cr, uid, ids, context)
        if not context.get('ignore_check_reconcile',False):
            result2 = self.check_and_reconcile(cr, uid, ids, context)        
        return result
    
    def _get_client_payment_attachment(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if ids:
            pn_id_list = ",".join(map(str,ids))
            cr.execute("""Select ai.id as id,
                           case when sum(case when coalesce(ia.attached_progress_sent,False) then 1 else 0 end) >0 then 1 else 0 end as attached_progress_sent,
                           case when sum(case when coalesce(ia.attached_progress_received,False) then 1 else 0 end) >0 then 1 else 0 end as attached_progress_received 
                               from
                                   account_invoice ai
                               left join
                                   ir_attachment ia on ai.id=ia.res_id and res_model='account.invoice'
                               where
                                   ai.id in (%s) 
                              group by ai.id""" % (pn_id_list))
            for pnl in cr.dictfetchall():
                res[pnl.pop('id')]=pnl
        return res
    
    def _get_attachement_link(self, cr, uid, ids, context=None):
        res={}
        for att_obj in self.pool.get('ir.attachment').browse(cr,uid,ids):
            if att_obj.res_model=='account.invoice' and att_obj.res_id:
                res[att_obj.res_id] = True
        return res.keys()
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    #Return ID and calculation for Ex. Rate
    def _get_clp_from_contract_currs(self, cr, uid, ids, context=None):
        result = []
        for cc in self.pool.get('kderp.contract.currency').browse(cr, uid, ids, context=context):
            if cc.contract_id:
                for clp in cc.contract_id.client_payment_ids:
                    result.append(clp.id)
        return list(set(result))
    
    def _get_clp_from_contract(self, cr, uid, ids, context=None):
        result = []
        for kcc in self.pool.get('kderp.contract.client').browse(cr, uid, ids, context=context):
            for clp in kcc.client_payment_ids:
                result.append(clp.id)
        return list(set(result))
    
    def _get_claim_exrate(self, cr, uid, ids, name, args, context=None):
        res = {}
        kcc_obj = self.pool.get('kderp.contract.currency')
        company_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        for clp in self.browse(cr, uid, ids, context):
            if clp.state<>'paid':
                res[clp.id]=kcc_obj.compute(cr, uid,clp.currency_id.id,company_currency_id, clp.contract_id.id, 1)
            else:
                receive_curr_id=False
                receive_curr_exrate=0
                received_amount=0
                res[clp.id]=0
                for kr in clp.received_ids:
                    receive_curr_id=kr.currency_id.id
                    receive_curr_exrate=kr.exrate
                    received_amount+=kr.amount
                    
                if company_currency_id==clp.currency_id.id:
                    res[clp.id]=1
                elif receive_curr_id==clp.currency_id.id:
                    res[clp.id]=receive_curr_exrate
                elif receive_curr_id!=clp.currency_id.id:
                    res[clp.id]=received_amount/clp.amount_total if clp.amount_total<>0 else 0
        return res
    
    #For field function Summary Amount in CLP
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount':0.0,
                'advanced':0.0,
                'retention':0.0
            }
            for line in invoice.invoice_line:
                price = line.amount * (1-(line.discount or 0.0)/100.0) + line.advanced + line.retention
                taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                amount = taxes['total']
                if line.invoice_id:
                    cur = line.invoice_id.currency_id
                    amount = cur_obj.round(cr, uid, cur, amount)

                res[invoice.id]['amount'] += line.amount
                res[invoice.id]['advanced'] += line.advanced
                res[invoice.id]['retention'] += line.retention                
                res[invoice.id]['amount_untaxed'] += line.amount+line.advanced+line.retention
                res[invoice.id]['amount_tax']+= line.amount_tax
            kderp_chk_cal_tax_first=True
            for line in invoice.tax_line:
                if kderp_chk_cal_tax_first:
                    kderp_chk_cal_tax_first=False
                    res[invoice.id]['amount_tax']=0.0
                res[invoice.id]['amount_tax'] += line.amount
            
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
        return res

    def _get_invoice_from_invoice(self, cr, uid, ids, context=None):
        result = []
        ai_ids=",".join(map(str,ids))
        cr.execute("""Select
                        trim(array_to_string(array_agg(ais.id::text),' ')) as res_ids
                    from
                        account_invoice ai
                    left join
                        account_invoice ais on ai.contract_id = ais.contract_id and ai.currency_id=ais.currency_id
                    where
                        ai.id in (%s)""" % ai_ids)
        for res_ids in cr.fetchall():
            if res_ids[0].isdigit():
                result.append(res_ids[0])
            else:
                tmp_list=res_ids[0]
                tmp_list=list(eval(tmp_list.strip().replace(' ',',').replace(' ','')))
                result.extend(tmp_list)
        
        return result
    
    def _get_issued(self, cr, uid, ids, name, args, context=None):
        res={}
        ai_ids=",".join(map(str,ids))
        cr.execute("""Select 
                            id,
                            coalesce((Select (sum(coalesce(amount_untaxed,0)),sum(coalesce(amount_tax,0)))
                        from
                            account_invoice ais
                        where 
                            ais.contract_id=ai.contract_id and ais.currency_id=ai.currency_id and ais.number<ai.number and coalesce(ais.number,'')<>''
                            and ais.state not in ('draft','cancel')
                        group by
                            ais.contract_id,
                            ais.currency_id),(0,0))
                    from 
                        account_invoice ai
                    where
                        ai.id in (%s)""" %(ai_ids))
        
        for id,issued_list in cr.fetchall():
            issued_list=eval(issued_list)
            res[id]={'issued_amount':issued_list[0],
                     'issued_vat':issued_list[1],
                     'issued_total':issued_list[0]+issued_list[1]}
        
        return res
    
    _columns = {
        'tax_base':fields.selection([('p','Progress'),('p_adv','Advance'),('p_retention','Retention'),('all','All')],'VAT Base on',required=True,readonly=True, states={'draft':[('readonly',False)]}),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Waiting for Payment'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Waiting for Payment\' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice. \
            \n* The \'Paid\' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled. \
            \n* The \'Cancelled\' status is used when user cancel invoice.'),

        'number': fields.char('Number',size=64,readonly=True, states={'draft':[('readonly',False)]}),
        'date_invoice': fields.date('Date', readonly=True, states={'draft':[('readonly',False)]}, select=True),
        
        'contract_id':fields.many2one('kderp.contract.client','Contract',required=True, readonly=True, states={'draft':[('readonly',False)]},ondelete='restrict'),
        'payment_term_id':fields.many2one('kderp.client.payment.term','Payment Term',required=True,ondelete='restrict'),

        'partner_id': fields.many2one('res.partner', 'Partner',ondelete='restrict', domain="[('customer','=',1)]",change_default=True, readonly=True, required=True, states={'draft':[('readonly',False)]}, track_visibility='always'),
        'owner_id':fields.many2one('res.partner','Owner',ondelete='restrict', domain="[('customer','=',1)]",readonly=True, states={'draft':[('readonly',False)]}),
        'address_id':fields.many2one('res.partner','Add',ondelete='restrict',readonly=True, states={'draft':[('readonly',False)]}),
        'invoice_address_id':fields.many2one('res.partner','Invoice Address',ondelete='restrict',readonly=True, states={'draft':[('readonly',False)]}),
        
        #VAT Invoice Allocated Amount
        'invoice_ids':fields.one2many("kderp.payment.vat.invoice","payment_id","Invoices",readonly=True,states={'draft':[('readonly',False)],'open':[('readonly',False)]}),
        
        'attached_progress_sent':fields.function(_get_client_payment_attachment,method=True,string='P.E.S. Sent',readonly=True,type='boolean',multi='client_payment_attachment',
                                             store={
                                                    'account.invoice':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','attached_progress_sent','attached_progress_received'],20)}),
              
        'attached_progress_received':fields.function(_get_client_payment_attachment,method=True,string='P.E.S. Received',readonly=True,type='boolean',multi='client_payment_attachment',
                                             store={
                                                    'account.invoice':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','attached_progress_sent','attached_progress_received'],20)}),
          
        'name':fields.text('Item of request',required=True,readonly=True, states={'draft':[('readonly',False)]}),
        'comment': fields.text('Remark'),
        
        'currency_id':fields.many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft':[('readonly',False)]}, track_visibility='always'),

        'exrate':fields.function(_get_claim_exrate, digits_compute=dp.get_precision('Percent'), string='Claim Ex.Rate',type='float',method=True,
                                store={
                                       'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['contract_id','currency_id','state'], 5),
                                       'kderp.contract.currency': (_get_clp_from_contract_currs, None, 5),
                                       'kderp.contract.client': (_get_clp_from_contract, ['contract_currency_ids'],5)                                       
                                       }),
 
        'amount':fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='Progress',type='float',method=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','tax_base'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id','amount','advanced','retention','price_subtotal'], 20),
            },
            multi='all'),
        'advanced':fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='Advanced',type='float',method=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','tax_base'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id','amount','advanced','retention','price_subtotal'], 20),
            },
            multi='all'),
        'retention':fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='Retention',type='float',method=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','tax_base'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id','amount','advanced','retention','price_subtotal'], 20),
            },
            multi='all'),
        
         'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='Subtotal', track_visibility='always',type='float',method=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','tax_base'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id','amount','advanced','retention','price_subtotal'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='VAT',type='float',method=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','tax_base'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id','amount','advanced','retention','price_subtotal'], 21),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='Total',type='float',method=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line','tax_base'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id','amount','advanced','retention','price_subtotal'], 21),
            },
            multi='all'),
                
        'issued_amount':fields.function(_get_issued, digits_compute=dp.get_precision('Amount'), string='Issued Amount',type='float',method=True,
                        store={
                            'account.invoice': (_get_invoice_from_invoice, None, 25)
                        },
                        multi='_get_issued'),
        'issued_vat':fields.function(_get_issued, digits_compute=dp.get_precision('Amount'), string='Issued VAT',type='float',method=True,
                        store={
                            'account.invoice': (_get_invoice_from_invoice, None, 25)
                        },
                        multi='_get_issued'),
        'issued_total':fields.function(_get_issued, digits_compute=dp.get_precision('Amount'), string='Issued Total',type='float',method=True,
                        store={
                            'account.invoice': (_get_invoice_from_invoice, None, 25)
                        },
                        multi='_get_issued'),
        }
    
    def _get_default_account(self,cr, uid, context={}):
        res = self.pool.get('account.account').search(cr,uid,[('type','=', 'receivable')])
        if res:
            res=res[0]
        return res
    
    _defaults={
               'tax_base':lambda *x:'p',
               'account_id':_get_default_account,
               'contract_id':lambda self,cr,uid,context={}:context.get('contract_id',False)
               }
    
    _sql_constraints = [
        ('client_payment_unique_no', 'unique(number)', 'Payment Number must be unique !'),
        #('cp_ctc_unique_no', 'unique(contract_id,currency_id,payment_term_id)', 'Contract, Payment, Currency must be unique !'),
        ]
    
    def onchange_curr(self, cr, uid, ids, curr_id=False):
        if curr_id:
            rc_obj=self.pool.get("res.currency")            
            result={'exrate':1.0 if rc_obj.browse(cr, uid,curr_id).name=='VND' else 0.0}
        else:
            result={'exrate':0.0}
        return {'value':result}
    
    def onchange_contract(self, cr, uid, ids, contract_id=False, currency_id=False,exrate=0):
        if contract_id:
            ctc = self.pool.get('kderp.contract.client').read(cr, uid, contract_id,['client_id','owner_id','address_id','invoice_address_id'])
            val={'partner_id':ctc['client_id'],'owner_id':ctc['owner_id'],
                 'address_id':ctc['address_id'],'invoice_address_id':ctc['invoice_address_id']}
        else:
            val={}
        if contract_id and currency_id:
            kcc_obj = self.pool.get('kderp.contract.currency')
            company_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
            exrate=kcc_obj.compute(cr, uid,currency_id,company_currency_id, contract_id, 1)
            val['exrate']=exrate
        return {'value':val}
    
    def onchange_date(self, cr, uid, ids, date, oldno):
        val={}
        if not oldno and date:
            cr.execute("""SELECT 
                            wnewcode.pattern || 
                            btrim(to_char(max(substring(wnewcode.code::text, length(wnewcode.pattern) + 1,padding )::integer) + 1,lpad('0',padding,'0'))) AS newcode
                        from
                            (
                            SELECT 
                            isq.name,
                            isq.code as seq_code,
                            isq.prefix || to_char(DATE '%s', suffix || lpad('_',padding,'_')) AS to_char, 
                            CASE WHEN cnewcode.code IS NULL 
                            THEN isq.prefix::text || to_char(DATE '%s', suffix || lpad('0',padding,'0'))
                            ELSE cnewcode.code
                            END AS code, 
                            isq.prefix::text || to_char(DATE '%s', suffix) AS pattern,
                            padding,
                            prefix
                            FROM 
                                ir_sequence isq
                            LEFT JOIN 
                            (SELECT 
                                account_invoice.number AS code
                            FROM 
                                account_invoice
                            WHERE
                                length(account_invoice.number::text)=
                                ((SELECT 
                                length(prefix || suffix) + padding AS length
                                FROM 
                                ir_sequence
                                WHERE 
                                ir_sequence.code::text = 'kderp_client_payment_code'::text LIMIT 1))
                            ) cnewcode ON cnewcode.code::text ~~ (isq.prefix || to_char(DATE '%s',  suffix || lpad('_',padding,'_')))
                            WHERE isq.code::text = 'kderp_client_payment_code'::text AND isq.active) wnewcode
                        GROUP BY 
                            pattern, 
                            name,
                            seq_code,
                            prefix,
                            padding;""" %(date,date,date,date))
            res = cr.fetchone()
            if res:
                val={'number':res[0]}
        return {'value':val}
        
      
    def btn_action_unpaid(self, cr, uid, ids, context={}):
        kr_obj=self.pool.get('kderp.received')
        for inv in self.browse(cr, uid, ids, context):
            for kr in inv.received_ids:
                kr_obj.action_unreconcile(cr, uid, [kr.id],context)
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        invoices = self.read(cr, uid, ids, ['move_id'])
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])
                
        self.write(cr, uid, ids, {'state':'cancel', 'move_id':False})
        if move_ids:
            # second, invalidate the move(s)
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            account_move_obj.unlink(cr, uid, move_ids, context=context)
        self._log_event(cr, uid, ids, -1.0, 'Cancel Invoice')
        return True
    
    def action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            try:
                wf_service.trg_delete(uid, 'account.invoice', inv_id, cr)
            except:
                continue
            wf_service.trg_create(uid, 'account.invoice', inv_id, cr)
        return True
    
    def action_revising_completed(self, cr, uid, ids, context={}):
        if context is None:
            context = {}

        self.action_date_assign(cr, uid, ids, context)
        self.action_move_create(cr, uid, ids, context)
        self.action_number(cr, uid, ids, context)
        self.invoice_validate(cr, uid, ids, context)
        return True
    
    def check_and_reconcile(self, cr, uid, ids, context):
        kr_obj = self.pool.get('kderp.received')
        for kcp in self.browse(cr, uid, ids):
            must_run =False
            kr_ids = []
            for kr in kcp.received_ids:
                must_run = True
                kr_ids.append(kr.id)
            
            if must_run:
                kr_obj.action_reconcile(cr, uid, kr_ids, context)
        return True
    
    def btn_action_revising_completed(self, cr, uid, ids, context):
        if not context: context={}
        self.action_revising_completed(cr, uid, ids, context)
        if not context.get('ignore_check_reconcile',False):
            self.check_and_reconcile(cr, uid, ids, context)        
        return True

#     def action_back_revising(self, cr, uid, ids, context={}):
#         if context is None:
#             context = {}
#         account_move_obj = self.pool.get('account.move')
#         invoices = self.read(cr, uid, ids, ['move_id'])
#                 
#         move_ids = [] # ones that we will need to remove
#         for i in invoices:
#             if i['move_id']:
#                 move_ids.append(i['move_id'][0])
# 
#         self.write(cr, uid, ids, {'move_id':False,'state':'revising'})
#         if move_ids:
#             # second, invalidate the move(s)
#             account_move_obj.button_cancel(cr, uid, move_ids, context=context)
#             # delete the move this invoice was pointing to
#             # Note that the corresponding move_lines and move_reconciles
#             # will be automatically deleted too
#             account_move_obj.unlink(cr, uid, move_ids, context=context)
# 
#         return True
    
account_invoice()

class account_invoice_line(osv.osv):

    _name = "account.invoice.line"
    _inherit="account.invoice.line"
    
    #Thay doi cach tinh ti gia
    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if not context:
            context={}
        
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        company_currency = inv.company_id.currency_id.id

        for line in inv.invoice_line:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)
            tax_code_found= False
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,
                    (line.price_unit * (1.0 - (line['discount'] or 0.0) / 100.0)),
                    line.quantity, line.product_id,
                    inv.partner_id)['taxes']:

                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = line.price_subtotal * tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = line.price_subtotal * tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(self.move_line_get_item(cr, uid, line, context))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                context.update({'invoice_id':invoice_id,'date': inv.date_invoice})
                res[-1]['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, tax_amount, context=context)
        return res
    
    def _price_amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = line.amount * (1-(line.discount or 0.0)/100.0) + line.advanced + line.retention
            #taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id] = price
            #if line.invoice_id:
             #   cur = line.invoice_id.currency_id
              #  res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
    
    def _price_amount_tax_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            if line.invoice_id.tax_base=='p':
                compute_amount= line.amount * (1-(line.discount or 0.0)/100.0)
            elif line.invoice_id.tax_base=='p_adv':
                compute_amount=line.advanced
            elif line.invoice_id.tax_base=='p_retention':
                compute_amount=line.retention
            else:
                compute_amount=line.price_unit
                
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id,compute_amount, 1, False, partner=line.invoice_id.partner_id)
            res[line.id]=0
            for tx in taxes['taxes']:
                res[line.id]+=tx['amount']
            #if line.invoice_id:
             #   cur = line.invoice_id.currency_id
              #  res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
    
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id] = taxes['total']
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res
    
    def _get_invoice(self, cr, uid, ids, context=None):
        result = {}
        for inv in self.pool.get('account.invoice').browse(cr, uid, ids, context=context):
            for line in inv.invoice_line:
                result[line.id] = True
        return result.keys()
    
    _columns={
              'invoice_line_tax_id': fields.many2many('account.tax', 'account_invoice_line_tax', 'invoice_line_id', 'tax_id', 'VAT (Round)', domain=[('parent_id','=',False)]),
              'account_analytic_id':fields.many2one('account.analytic.account', 'Job',required=True),
              'invoice_id': fields.many2one('account.invoice', 'Invoice Reference', ondelete='cascade', required=True,select=True),

              'advanced': fields.float('Advanced', required=True, digits_compute= dp.get_precision('Product Price')),
              'retention': fields.float('Retention', required=True, digits_compute= dp.get_precision('Product Price')),
              'amount': fields.float('Amount', required=True, digits_compute= dp.get_precision('Product Price')),
              'name':fields.char('Description', required=True, size=128),
    
              'price_unit': fields.function(_price_amount_line, string='Amount', type="float",digits_compute= dp.get_precision('Amount'),
                                                store={
                                                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids,['amount','price_unit','invoice_line_tax_id','quantity','discount','invoice_id','advanced','retention','price_subtotal'], 20),
                                                        'account.invoice': (_get_invoice, ['tax_base'], 20)}),
              'amount_tax': fields.function(_price_amount_tax_line, string='VAT (Auto)', type="float",digits_compute= dp.get_precision('Amount'),
                                                store={
                                                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids,['amount','price_unit','invoice_line_tax_id','quantity','discount','invoice_id','advanced','retention','price_subtotal'], 20),
                                                        'account.invoice': (_get_invoice, ['tax_base'], 20)}),
              'price_subtotal': fields.function(_price_amount_line, string='Sub-Total', type="float",digits_compute= dp.get_precision('Amount'),
                                                store={
                                                        'account.invoice.line': (lambda self, cr, uid, ids, c={}: ids,['amount','price_unit','invoice_line_tax_id','quantity','discount','invoice_id','advanced','retention','price_subtotal'], 20),
                                                        'account.invoice': (_get_invoice, ['tax_base'], 20)}),
              }

    def onchange_analytic(self, cr, uid, ids, analytic_id=False):
        if not analytic_id:
            val=''
        else:
            val=self.pool.get('account.analytic.account').read(cr, uid, analytic_id,['name'])['name']
        return {'value':{'name':val}}
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            ids = self.search(cr, user, [('account_analytic_id',operator,name)]+ args, limit=limit, context=context)
            
            if not ids:
                check=name.replace(',','')
                if check.isdigit():
                    ids = self.search(cr, user, [('price_unit','=',check)]+ args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
account_invoice_line()
