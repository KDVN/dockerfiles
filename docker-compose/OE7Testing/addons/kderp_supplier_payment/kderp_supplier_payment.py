from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null

import openerp.exceptions

try:
    from kderp_base.amount_to_text import *
except:
    pass

import time
import datetime

class account_move(osv.osv):
    _name = "account.move"
    _description = "Account Entry"
    _order = 'id desc'
    _inherit='account.move'
     
    def post_supplier(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        prefix = context.get('paid_string','')
        valid_moves = self.validate(cr, uid, ids, context)
     
        if not valid_moves:
            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name =='/':
                new_name = False
                journal = move.journal_id
 
                if invoice and invoice.name:
                    new_name = prefix + " " + invoice.name
                else:
                    if journal.sequence_id:
                        c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                        new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                    else:
                        raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))
 
                if new_name:
                    self.write(cr, uid, [move.id], {'name':new_name.strip()})
 
        cr.execute('UPDATE account_move '\
                   'SET state=%s '\
                   'WHERE id IN %s',
                   ('posted', tuple(valid_moves),))
        return True
account_move()
    
class kderp_supplier_payment(osv.osv):
    _name = 'kderp.supplier.payment'
    _description = 'Supplier Payment for Kinden'

    #SYSTEM METHOD
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for t in invoices:
            if t['state'] not in ('draft', 'cancel'):
                raise openerp.exceptions.Warning('You cannot delete an Supplier Payment which is not draft or cancelled.')
            else:
                unlink_ids.append(t['id'])

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids=[]
            ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids=self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        
        reads = self.read(cr, uid, ids, ['name'], context=context)
        res = []
        for record in reads:
            name = record['name'].strip() if record['name'] else 'Not Avaible Number' 

            res.append((record['id'], name))
        return res
    
    def create(self, cr, uid, vals, context={}):
        res=osv.osv.create(self, cr, uid, vals, context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return res
    
    def write(self, cr, uid, ids, vals, context={}):
        if vals:
            if len(ids)>0 and 'date_bc_to_acc' in context and 'bc_to_accounting_date' not in vals:
                if context.get('date_bc_to_acc',False):
                    vals['bc_to_accounting_date']=context['date_bc_to_acc']
        if 'wkf' in context:
            for ksp in self.browse(cr, uid, ids,context):
                new_val = vals
                if ksp.bc_to_accounting_date:
                    if  'bc_to_accounting_date' in new_val:
                        pop_date = new_val.pop('bc_to_accounting_date')
                osv.osv.write(self, cr, uid, [ksp.id],new_val,context=context)
        else:
            osv.osv.write(self, cr, uid, ids, vals, context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return True
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'name': False,
            'state':'draft',
            'kderp_vat_invoice_ids':False,
            'payment_line':False,
            'tax_line_ids':False,
            'payment_ids': False,
            'move_id': False          
        })
        return super(kderp_supplier_payment, self).copy(cr, uid, id, default, context)
    
    #METHOD FOR WORKFLOW
    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        :param invoice_browse: browsable record of the invoice that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this invoice
        """
        return move_lines
    
    def group_lines(self, cr, uid, iml, line, inv):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        if inv.journal_id.group_invoice_lines:
            line2 = {}
            for x, y, l in line:
                tmp = self.inv_line_characteristic_hashcode(inv, l)

                if tmp in line2:
                    am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                    line2[tmp]['debit'] = (am > 0) and am or 0.0
                    line2[tmp]['credit'] = (am < 0) and -am or 0.0
                    line2[tmp]['tax_amount'] += l['tax_amount']
                    line2[tmp]['analytic_lines'] += l['analytic_lines']
                else:
                    line2[tmp] = l
            line = []
            for key, val in line2.items():
                line.append((0,0,val))
        return line
    
    def move_line_get_item(self, cr, uid, line, context=None):
        return {
            'type':'src',
            'name': line.name,
            'price_unit':line.price_unit,
            'quantity':line.quantity,
            'price':line.price_subtotal,
            'account_id':line.account_id.id,
            'product_id':line.product_id.id,
            'uos_id':line.uos_id.id,
            'account_analytic_id':line.account_analytic_id.id,
            'taxes':line.invoice_line_tax_id,
        }
    
    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = []
        if not context:
            context={}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')

        ksp = self.browse(cr, uid, invoice_id, context=context)
        exrate = context.get('new_exrate',0) if context.get('new_exrate',0)>0 else ksp.order_id.exrate 
        company_currency = self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id.id
        if ksp.payment_line:
            count_payment_line=0
            for kspl in ksp.payment_line:
                count_payment_line+=1
                mres ={
                        'type':'src',
                        'name':ksp.name,
                        'price_unit':kspl.amount,
                        'quantity':1,
                        'price':kspl.amount,
                        'account_id':ksp.expense_account_id.id,
                        'product_id':False,
                        'uos_id':False,
                        'account_analytic_id':kspl.account_analytic_id.id,
                        'taxes':False}
                if not mres:
                    continue
                res.append(mres)
                tax_code_found= False
                payment_per_vat = kspl.amount/ksp.sub_total if ksp.sub_total else 0
                if payment_per_vat:
                    for tax in tax_obj.compute_all(cr, uid, ksp.taxes_id,kspl.amount,
                            1, False,
                            False)['taxes']:            
                        tax_code_id = tax['base_code_id']
                        tax_amount = (kspl.amount*payment_per_vat * tax['base_sign'])
        
                        if tax_code_found:
                            if not tax_code_id:
                                continue
                            res.append({
                                        'type':'src',
                                        'name':ksp.name,
                                        'price_unit':kspl.amount,
                                        'quantity':1,
                                        'price':kspl.amount,
                                        'account_id':ksp.expense_account_id.id,
                                        'product_id':False,
                                        'uos_id':False,
                                        'account_analytic_id':kspl.account_analytic_id.id,
                                        'taxes':False})
                            res[-1]['price'] = 0.0
                            res[-1]['account_analytic_id'] = False
                        elif not tax_code_id:
                            continue
                        tax_code_found = True
            
                        res[-1]['tax_code_id'] = tax_code_id
                        res[-1]['tax_amount'] = cur_obj.round(cr, uid, self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id, tax_amount*exrate)
                elif (payment_per_vat==0 and count_payment_line and ksp.taxes_id):
                     amount_tax=0.0
                     for tax in tax_obj.compute_all(cr, uid, ksp.taxes_id,1,
                            1, False,
                            False)['taxes']:

                        tax_code_id = tax['base_code_id']
                        tax_amount = (kspl.amount * tax['base_sign'])
                        #raise osv.except_osv("E",tax)
                        if tax_code_found:
                            if not tax_code_id:
                                continue
                            res.append({
                                        'type':'src',
                                        'name':ksp.name,
                                        'price_unit':0,
                                        'quantity':1,
                                        'price':kspl.amount,
                                        'account_id':ksp.expense_account_id.id,
                                        'product_id':False,
                                        'uos_id':False,
                                        'account_analytic_id':kspl.account_analytic_id.id,
                                        'taxes':False})
                            res[-1]['price'] = 0.0
                            res[-1]['account_analytic_id'] = False
                        elif not tax_code_id:
                            continue
                        tax_code_found = True
                        
                        res[-1]['tax_code_id'] = tax_code_id
                        res[-1]['tax_amount'] = cur_obj.round(cr, uid, self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id, tax_amount*exrate)
        elif ksp.taxes_id:
            amount_tax=0.0
            tax_code_found= False
            res.append({
                        'type':'src',
                        'name':ksp.name,
                        'price_unit':0,
                        'quantity':1,
                        'price':0,
                        'account_id':ksp.expense_account_id.id,
                        'product_id':False,
                        'uos_id':False,
                        'account_analytic_id':False,
                        'taxes':False})
            for tax in tax_obj.compute_all(cr, uid, ksp.taxes_id,1,
                   1, False,
                   False)['taxes']:
            
               tax_code_id = tax['base_code_id']
               tax_amount = (0 * tax['base_sign'])
               #raise osv.except_osv("E",tax)
               if tax_code_found:
                   if not tax_code_id:
                       continue
                   res.append({
                               'type':'src',
                               'name':ksp.name,
                               'price_unit':0,
                               'quantity':1,
                               'price':0,
                               'account_id':ksp.expense_account_id.id,
                               'product_id':False,
                               'uos_id':False,
                               'account_analytic_id':False,
                               'taxes':False})
                   res[-1]['price'] = 0.0
                   res[-1]['account_analytic_id'] = False
               elif not tax_code_id:
                   continue
               tax_code_found = True
               
               res[-1]['tax_code_id'] = tax_code_id
               res[-1]['tax_amount'] = cur_obj.round(cr, uid, self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id, tax_amount*exrate)
        else:
            raise osv.except_osv("E","Not Avaiable Line") 
            payment_per = ksp.sub_total/ksp.order_id.final_price if ksp.order_id.final_price else 0 #Tinh % 1 payment amount /po amount
            payment_per_vat = ksp.amount/ksp.order_id.final_price if ksp.order_id.final_price else 0
            cr.execute("""Select 
                                account_analytic_id,
                                sum(coalesce(final_subtotal,0)) 
                            from 
                                purchase_order_line where order_id in (%s) group by account_analytic_id""" % (ksp.order_id.id))
            for aaa_id,amount in cr.fetchall():
                mres ={
                        'type':'src',
                        'name':ksp.name,
                        'price_unit':amount*payment_per,
                        'quantity':1,
                        'price':amount*payment_per,
                        'account_id':ksp.expense_account_id.id,
                        'product_id':False,
                        'uos_id':False,
                        'account_analytic_id':aaa_id,
                        'taxes':False}
                if not mres:
                    continue
                res.append(mres)
                tax_code_found= False

                if payment_per_vat>0:
                    for tax in tax_obj.compute_all(cr, uid, ksp.taxes_id,amount*payment_per,
                            1, False,
                            False)['taxes']:            
                        tax_code_id = tax['base_code_id']
                        tax_amount = (payment_per_vat*amount * tax['base_sign'])
        
                        if tax_code_found:
                            if not tax_code_id:
                                continue
                            res.append({
                                        'type':'src',
                                        'name':ksp.name,
                                        'price_unit':amount*payment_per,
                                        'quantity':1,
                                        'price':amount*payment_per,
                                        'account_id':ksp.expense_account_id.id,
                                        'product_id':False,
                                        'uos_id':False,
                                        'account_analytic_id':aaa_id,
                                        'taxes':False})
                            res[-1]['price'] = 0.0
                            res[-1]['account_analytic_id'] = False
                        elif not tax_code_id:
                            continue
                        tax_code_found = True
            
                        res[-1]['tax_code_id'] = tax_code_id
                        res[-1]['tax_amount'] = cur_obj.round(cr, uid, self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id, tax_amount*exrate)
        return res
 
    def _get_analytic_lines(self, cr, uid, id, context=None):
        if context is None:
            context = {}
        ksp = self.browse(cr, uid, id)
        cur_obj = self.pool.get('res.currency')
        exrate = context.get('exrate',0) if context.get('exrate',0) else ksp.order_id.exrate
        company_currency = self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id.id

        sign = -1

        iml = self.move_line_get(cr, uid, ksp.id, context=context)
        
        for il in iml:
            if il['account_analytic_id']:
                ref = ksp.name
                if not ksp.journal_id.analytic_journal_id:
                    raise osv.except_osv(_('No Analytic Journal!'),_("You have to define an analytic journal on the '%s' journal!") % (ksp.journal_id.name,))
                il['analytic_lines'] = [(0,0, {
                    'name': il['name'],
                    'date': ksp.date,
                    'account_id': il['account_analytic_id'],
                    'unit_amount': il['quantity'],
                    'amount':  cur_obj.round(cr, uid,self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id , il['price']*exrate)*sign,
                    'product_id': il['product_id'],
                    'product_uom_id': il['uos_id'],
                    'general_account_id': il['account_id'],
                    'journal_id': ksp.journal_id.analytic_journal_id.id,
                    'ref': ref,
                })]
        return iml
    
    def line_get_convert(self, cr, uid, x, part, date, context=None):
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', []),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
        }
        
    def compute_invoice_totals(self, cr, uid, inv, company_currency, ref, invoice_move_lines, context=None):
        if context is None:
            context={}
        total = 0
        total_currency = 0
        cur_obj = self.pool.get('res.currency')
        exrate = context.get('new_exrate',0) if context.get('new_exrate',0) else inv.exrate
        for i in invoice_move_lines:
            if inv.currency_id.id != company_currency:
                context.update({'date': inv.date or time.strftime('%Y-%m-%d')})
                i['currency_id'] = inv.currency_id.id
                i['amount_currency'] = i['price']
                i['price'] = cur_obj.round(cr, uid, self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id ,i['price']*exrate)
            else:
                i['amount_currency'] = False
                i['currency_id'] = False
            i['ref'] = ref

            total -= i['price']
            total_currency -= i['amount_currency'] or i['price']
        
        return total, total_currency, invoice_move_lines
    
    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        if not context: context = {}

        vat = self.update_supplier_taxes(cr, uid, ids, context)
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        
    #    payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        company =  self.pool['res.users'].browse(cr, uid, uid).company_id

        for ksp in self.browse(cr, uid, ids, context=context):

            exrate = context.get('new_exrate',0) if context.get('new_exrate',0)>0 else ksp.order_id.exrate
            if not ksp.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if ksp.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': ksp.order_id.partner_id.lang})
            #if not ksp.date:
             #   self.write(cr, uid, [ksp.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = company.currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, ksp.id, context=ctx)
            
            # check if taxes are all computed
            #raise osv.except_osv("E",iml)
        
            #compute_taxes = ait_obj.compute(cr, uid, ksp.id, context=ctx)
            
            #self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            #group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            #group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            #if group_check_total and uid in [x.id for x in group_check_total.users]:
            #    if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
            #        raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            #if inv.payment_term:
            #    total_fixed = total_percent = 0
            #    for line in inv.payment_term.line_ids:
            #        if line.value == 'fixed':
            #            total_fixed += line.value_amount
            #        if line.value == 'procent':
            #            total_percent += line.value_amount
            #    total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
            #    if (total_fixed + total_percent) > 100:
            #        raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))
            
            # one move line per tax line
            iml += ait_obj.move_line_get_supplier_payment(cr, uid, ksp.id)
            #raise osv.except_osv("EEEEEEEEEEEE", ait_obj.move_line_get_supplier_payment(cr, uid, ksp.id))
            entry_type = ''
            ref = ksp.name
            entry_type = 'journal_pur_voucher'

            diff_currency_p = ksp.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, ksp, company_currency, ref, iml, context=ctx)
            acc_id = ksp.account_id.id
            #raise osv.except_osv("EEEEEEFF",iml)
            name = ksp.name
            totlines = False
            
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': ksp.date})
                for t in totlines:
                    if ksp.currency_id.id != company_currency:
                        amount_currency = cur_obj.round(cr, uid, company.currency_id,t[1]/exrate) if exrate else 0  #cur_obj.compute(cr, uid, company_currency, ksp.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': ksp.due_date or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and ksp.currency_id.id or False,
                    'ref': ref
            })
            
            date = ksp.date or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(ksp.order_id.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, ksp)
            
            journal_id = ksp.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, ksp, line)
            
            move = {
                'ref': ksp.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': ksp.description,
                'company_id': company.id,
            }
            period_id = ksp.period_id and ksp.period_id.id or False
            ctx.update(company_id=company.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, ksp.date, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
                    
            ctx.update(invoice=ksp)
            
            
            #raise osv.except_osv("E",move)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            #raise osv.except_osv("E",move)
        
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            #raise osv.except_osv("E",move)
            # make the invoice point to that move
            self.write(cr, uid, [ksp.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post_supplier(cr, uid, [move_id], context=ctx)
        
        return True
    
    def check_and_reconcile(self, cr, uid, ids, *args):
        kp_obj = self.pool.get('kderp.supplier.payment.pay')
        for ksp in self.browse(cr, uid, ids):
            must_run =False
            kp_ids = []
            for kp in ksp.payment_ids:
                must_run = True
                kp_ids.append(kp.id)
            if must_run:
                kp_obj.action_reconcile(cr, uid, kp_ids, context={})
        return True
    
    def btn_action_revising_completed(self, cr, uid, ids, context={}):
        if not context: context={}
        self.action_revising_completed(cr, uid, ids, context)
        self.check_and_reconcile(cr, uid, ids, context)        
        return True

    def action_revising_completed(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        self.wkf_action_payment_done(cr, uid, ids, context)
        self.action_move_create(cr, uid, ids, context)        
        return True
    
    def action_back_revising(self, cr, uid, ids, context={}):
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        invoices = self.read(cr, uid, ids, ['move_id'])
                
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])

        self.write(cr, uid, ids, {'move_id':False,'state':'revising'})
        if move_ids:
            # second, invalidate the move(s)
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            account_move_obj.unlink(cr, uid, move_ids, context=context)

        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        invoices = self.read(cr, uid, ids, ['move_id'])
        vat_invoices=self.read(cr, uid,ids,['kderp_vat_invoice_ids'])

        for vi in vat_invoices:
            if vi['kderp_vat_invoice_ids']:
                self.pool.get('kderp.supplier.vat.invoice').write(cr, uid, vi['kderp_vat_invoice_ids'],{'state':'draft'})
                
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])
#             if i['payment_ids']:
#                 account_move_line_obj = self.pool.get('account.move.line')
#                 pay_ids = account_move_line_obj.browse(cr, uid, i['payment_ids'])
#                 for move_line in pay_ids:
#                     if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
#                         raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids
        self.write(cr, uid, ids, {'move_id':False})
        if move_ids:
            # second, invalidate the move(s)
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            account_move_obj.unlink(cr, uid, move_ids, context=context)
            
        self.write(cr, uid, ids, {'state':'cancel'})
#         wf_service = netsvc.LocalService("workflow")
#         for ksp_id in ids:
#             try:
#                 wf_service.trg_delete(uid, 'kderp.supplier.payment', ksp_id, cr)
#             except:
#                 continue        
        return True
    
    #PM Checking - BOD Checking
    def wkf_action_pmchecking_bodchecking(self,cr,uid,ids,*args): #For Workflow
        dt = None
        if args:
            ctx=args[0]
            if ctx:
                if 'date' in ctx:
                    dt = ctx['date']
        self.write(cr, uid, ids, {'state' : 'waiting_bod', 'to_bc_date_second' : dt})
        return True
    
    def wkf_action_payment_done(self, cr, uid, ids, *args):
        list=[]
        for ksp in self.browse(cr, uid, ids):
            if ksp.payment_type=='na':
                list.append(str(ksp.name))
        if list: raise osv.except_osv("KDERP Warning","Please choose Payment type before submit ! %s " % list)
        
        ctx={'date_bc_to_acc': time.strftime('%Y-%m-%d'),'wkf':True}
        self.write(cr,uid,ids,{'state':'completed'},context=ctx)
        return True
    
    def wkf_action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            wf_service.trg_create(uid, 'kderp.supplier.payment', inv_id, cr)
        return True
    
    #METHOD FOR FIELD FUNCTION    
    def _compute_lines(self, cr, uid, ids, name, args, context=None):
        result = {}
        for ksp in self.browse(cr, uid, ids, context=context):
            src = []
            lines = []
            if ksp.move_id:
                for m in ksp.move_id.line_id:
                    temp_lines = []
                    if m.reconcile_id:
                        temp_lines = map(lambda x: x.id, m.reconcile_id.line_id)
                    elif m.reconcile_partial_id:
                        temp_lines = map(lambda x: x.id, m.reconcile_partial_id.line_partial_ids)
                    lines += [x for x in temp_lines if x not in lines]
                    src.append(m.id)

            lines = filter(lambda x: x not in src, lines)
            result[ksp.id] = lines
        return result
    
    def _get_summary_amount(self, cr, uid, ids, name, args, context={}):
        res={}
        tax_obj =self.pool.get('account.tax')
        cur_obj=self.pool.get('res.currency')
        for ksp in self.browse(cr, uid, ids,context):
            amount_tax=0
            
            if ksp.tax_base=='p':
                val_amount=ksp.amount
            elif ksp.tax_base=='p_adv':
                val_amount=ksp.advanced_amount
            elif ksp.tax_base=='p_retention':
                val_amount=ksp.retention_amount
            else:
                val_amount=ksp.amount + ksp.advanced_amount + ksp.retention_amount
            if ksp.taxes_id:
                val=0.0
                for c in tax_obj.compute_all(cr, uid, ksp.taxes_id, val_amount, 1, False, False)['taxes']:
                    val += c.get('amount', 0.0)
                
                amount_tax=cur_obj.round(cr, uid, ksp.currency_id, val) if ksp.currency_id else val
                
            res[ksp.id]={'sub_total':ksp.amount + ksp.advanced_amount + ksp.retention_amount,
                         'amount_tax':amount_tax,
                        'total': ksp.amount + ksp.advanced_amount + ksp.retention_amount + amount_tax }
        return res
    
    def _amount_to_word(self, cr, uid, ids, name, args, context={}):
        res = {}
        for x in self.browse(cr,uid,ids, context=context):
            total=x.total if x.total>=0 else 0
            if x.currency_id.name=='USD':
                amount_to_word_vn = amount_to_text(total,'vn'," dollar").capitalize()
                amount_to_word_en = amount_to_text(total,'en'," dollar").capitalize()
            elif x.currency_id.name=='VND':
                amount_to_word_vn = amount_to_text(total,'vn', u' \u0111\u1ed3ng').capitalize()  # + x.currency_id.name
                amount_to_word_en = amount_to_text(total,"en","dongs").capitalize()
            else:
                amount_to_word_vn =amount_to_text(total,'vn'," " + x.currency_id.name).capitalize()
                amount_to_word_en =amount_to_text(total,'en'," "+ x.currency_id.name).capitalize() 
            res[x.id] = {'amount_to_word_vnd':amount_to_word_vn,
                         'amount_to_word_usd':amount_to_word_en}
        return res
    
    def _get_sno_year(self, cr, uid, ids, name, args, context={}):
        res = {}
        for ksp in self.browse(cr, uid, ids, context):
            try:
                sno=int(ksp.name[5:])
            except:
                sno=0
            try:
                year=ksp.name[2:4]
            except:
                year=""
            
            res[ksp.id]={'number': sno,'year': year}
            
        return res
    
    def _get_exrate(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for rop in self.browse(cr,uid,ids):
            company_currency = rop.order_id.company_id.currency_id.id
            from_curr = rop.currency_id.id
            compute_date = rop.order_id.date_order
            res[rop.id] = cur_obj.compute(cr, uid, from_curr, company_currency, 1, round=False,context={'date': compute_date})
        return res
    
    #METHOD ONCHANGE
    def _onchange_due_date(self, cr, uid, ids,rop_date_str):
        if rop_date_str:
            from datetime import datetime as ldatetime
            rop_date = ldatetime.strptime(rop_date_str, '%Y-%m-%d')           
            m = rop_date.month
            d = rop_date.day
            y = rop_date.year
            if m==12 :
                if (d>25):
                    m = 2
                    y = y + 1
                    d = 10                                
                elif (d<11):
                    m = 1
                    y = y + 1
                    d = 10
                else:
                    m = 1
                    y = y + 1
                    d = 25                            
            elif m==11:
                if (d>25):
                    m = 1
                    y = y + 1
                    d = 10
                elif (d<11):
                    m= m +1
                    d = 10
                else:
                    m= m +1
                    d= 25
            else:
                if (d>25):
                    m = m + 2
                    d = 10
                elif (d<11):
                    m = m + 1
                    d = 10
                else:
                    m = m + 1
                    d = 25 
            due_date = datetime.date(y, m, d).strftime("%Y-%m-%d")
            #raise osv.except_osv(,due_date)
        else:
            due_date = False
        #raise osv.except_osv("E",{'value':{'due_date':due_date}})    
        return due_date
            
    def onchange_date(self, cr, uid, ids, date, oldno):
        cr.execute("Select location_user from res_users where id=%s" % uid)
        res = cr.fetchone()[0]
        chk_ignore =  False
        due_date = date
        
        if due_date and not chk_ignore:
            #due_date = self.pool.get('kdvn.common.function').check_date(date)
            due_date = self._onchange_due_date(cr,uid,ids,date)
        
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
                                kderp_supplier_payment.name AS code
                            FROM 
                                kderp_supplier_payment
                            WHERE
                                length(kderp_supplier_payment.name::text)=
                                ((SELECT 
                                length(prefix || suffix) + padding AS length
                                FROM 
                                ir_sequence
                                WHERE 
                                ir_sequence.code::text = 'kderp_supplier_payment_code'::text LIMIT 1))
                            ) cnewcode ON cnewcode.code::text ~~ (isq.prefix || to_char(DATE '%s',  suffix || lpad('_',padding,'_')))
                            WHERE isq.code::text = 'kderp_supplier_payment_code'::text AND isq.active) wnewcode
                        GROUP BY 
                            pattern, 
                            name,
                            seq_code,
                            prefix,
                            padding;""" %(date,date,date,date))
            res = cr.fetchone()
            if res:
                val={'name':res[0]}
        if due_date:
            val['due_date']=due_date
        return {'value':val}
    
    #METHOD FOR DEFAULT
    def _get_journal(self, cr, uid, context=None):
        if context is None:
            context = {}
        type_inv =  'in_invoice'
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company_id = context.get('company_id', user.company_id.id)
        type2journal = {'in_invoice': 'purchase', 'in_refund': 'purchase_refund'}
        journal_obj = self.pool.get('account.journal')
        domain = [('company_id', '=', company_id)]
        if isinstance(type_inv, list):
            domain.append(('type', 'in', [type2journal.get(type) for type in type_inv if type2journal.get(type)]))
        else:
            domain.append(('type', '=', type2journal.get(type_inv, 'sale')))
        res = journal_obj.search(cr, uid, domain, limit=1)
        return res and res[0] or False
    
    def _default_expense_account_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        prop = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category', context=context)
        return prop and prop.id or False
    
    def _get_default_account(self,cr, uid, context={}):
        res = self.pool.get('account.account').search(cr,uid,[('type','=', 'payable')])
        if res:
            res=res[0]
        return res
    
    def _get_payment_type(self, cr, uid, context={}):
        if not context:
            context={}
        cr.execute("""SELECT uid
                              FROM res_groups_users_rel 
                                  where gid in( select id from res_groups where name ='KDERP - Supplier Payment Read Only Bankstransfer')
                            and uid =%s
                            """%(uid))
        if cr.rowcount !=0:  
            payment_type='cash'     
        else:
            payment_type='bank'   
        return payment_type
    
    _order = 'year desc, number desc, name desc'
    
    _columns={
              #Code Filed Area
              'name':fields.char('R.O.P. No.',size=25, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              
              'number':fields.function(_get_sno_year,type='integer',method=True,string='No.',multi='_get_sno_year',
                                       store={'kderp.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['name'], 10)}),
                                                 
              'year':fields.function(_get_sno_year,string='Year',method=True,type='char',size=4,multi='_get_sno_year',
                                     store={'kderp.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['name'], 10)}),
              
              'payee':fields.char('Payee',size=64),
              
              'payment_type':fields.selection([('bank','Bankstransfer'),('cash','Cash'),('na','Not Available')],'Payment type', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},required=True),

              'description':fields.text('Description', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'date':fields.date('R.O.P. Date', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              
              'due_date':fields.date('Due Date', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),

              'amount':fields.float('Amount', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},digits_compute=dp.get_precision('Amount')),
              'advanced_amount':fields.float('Advanced',digits_compute=dp.get_precision('Amount'), states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'retention_amount':fields.float('Retention',digits_compute=dp.get_precision('Amount'), states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),  

              'exrate':fields.function(_get_exrate,type='float',method=True,string='Ex.Rate',
                                       store={'kderp.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['date','currency_id','order_id'], 10)}),

              'sub_total':fields.function(_get_summary_amount,string='Sub-Total',digits_compute=dp.get_precision('Amount'),
                                   method=True,type='float',size=4,multi='_get_summary_amount',
                                  store={'kderp.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['amount','advanced_amount','retention_amount','currency_id'], 10)}),
              
              'amount_tax':fields.function(_get_summary_amount,string='VAT Amt',digits_compute=dp.get_precision('Amount'),
                                   method=True,type='float',size=4,multi='_get_summary_amount',
                                  store={'kderp.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['amount','advanced_amount','retention_amount','taxes_id','tax_base','currency_id'], 5)}),
              
              'total':fields.function(_get_summary_amount,string='Total',digits_compute=dp.get_precision('Amount'),
                                   method=True,type='float',size=4,multi='_get_summary_amount',
                                  store={'kderp.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['amount','advanced_amount','retention_amount','taxes_id','tax_base','currency_id'], 10)}),

              'amount_to_word_vnd':fields.function(_amount_to_word,string='In VND',method=True,type='char',size=1000,multi="_get_multi_to_word"),
              'amount_to_word_usd':fields.function(_amount_to_word,string='In USD',method=True,type='char',size=1000,multi="_get_multi_to_word"),
              
              'pro_to_acc':fields.date("To Accounting", states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is Procurement send document to Accounting for Tax Declaration'),
              'to_bc_date_first':fields.date('First Date to B.C.', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is Procurement send document to Buddget Control for checking Budget'),
              'bc_checked_date':fields.date('B.C. Checked Date', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is BC Dept. passed.'),
              'to_site_date':fields.date('To Site Date', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is Procurement send document to Site for Project Manager confirmation'),
              'from_site_date':fields.date('From Site Date', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is document return to Procurement from Site'),
              'to_procurement_manager':fields.date('To Pro. Manager', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is Submit document to Procurement Manager'),
              'to_bc_date_second':fields.date('Second Date to B.C.', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is Procurement send Budget Control for B.O.D. confirmation'),
              'bc_to_accounting_date':fields.date('Date B.C. to Acc.', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},help='This date is Budget Control sent to Accouting for Payment to supplier'),
              
              'move_name': fields.char('Journal Entry', size=64, readonly=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
          
              'state': fields.selection([
                                        ('draft','Draft'),
                                        ('pr_dept_checking','Pro. checking'),
                                        ('submitting','BC checking'), #Submiting ->BC Checking
                                        ('bc_passed','BC checked'),
                                        ('bc_checked','PM checking'),
                                        ('waiting_bod','BOD checking'),#Waiting for B.O.D. confirmation->BOD Checking
                                        ('completed','BOD approved'), #BOD approved->Completed
                                        ('revising','Revising'),
                                        ('paid','Paid'),
                                        ('done','Paid'),
                                        ('cancel','Rejected')],'State', select=True, readonly=True),
              #Relation Field              
              #Accounting
              'supplier_id': fields.related('order_id', 'partner_id', type='many2one',relation='res.partner', string='Supplier',readonly=True),
              'account_id': fields.many2one('account.account', 'Account', required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}, help="The partner account used for this invoice."),
              'move_id': fields.many2one('account.move', 'Detail', readonly=True, select=1,ondelete='restrict'),
              'journal_id': fields.many2one('account.journal', 'Journal', required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]},domain=[('type','=','purchase')]),              
              'expense_account_id': fields.many2one('account.account', 'Expense Acc.', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], help="Expense account related to the selected product.", states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True, states={'draft':[('readonly',False)]}),
              
              'currency_id':fields.many2one('res.currency','Currency',required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              
              'user_create_id':fields.many2one("res.users","Create User"),
              'order_id':fields.many2one('purchase.order','PO',required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'user_applicant_id':fields.many2one('res.users','Applicant User', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'tax_base':fields.selection([('p','Progress'),('p_adv','Advance'),('p_retention','Retention'),('all','All')], 'VAT Base', required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'taxes_id': fields.many2many('account.tax', 'supplier_payment_tax', 'supplier_payment_id', 'tax_id', 'Taxes', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'kderp_vat_invoice_ids':fields.many2many('kderp.supplier.vat.invoice','kderp_supplier_payment_vat_invoice_rel', 'payment_id', 'vat_invoice_id', 'VAT Invoices',states={'cancel':[('readonly',True)]},ondelete='restrict'),
              
              #'payment_ids': fields.function(_compute_lines, relation='account.move.line', type="many2many", string='Payments'),
              
              'payment_line':fields.one2many('kderp.supplier.payment.line','supplier_payment_id','Detail of payemnt', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)],'done':[('readonly',True)]}),
              'tax_line_ids': fields.one2many('account.invoice.tax', 'supplier_invoice_id', 'Tax Lines', readonly=True, states={'draft':[('readonly',False)]}),
              
              #Calculation in Line
              'base_on_line':fields.boolean('Base on Line',states={'cancel':[('readonly',True)]})
              }
    _sql_constraints = [('supplier_payment_unique_no', 'unique(name)', 'Supplier Payment Number must be unique !')]
        
    def _check_job_budget(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        job_ids=[]
        if not obj.base_on_line:
            for kspl in obj.payment_line:
                job_id = kspl.account_analytic_id.id
                if job_id in job_ids:
                    return False
                else:
                    job_ids.append(job_id)
        else:
            for kspl in obj.payment_line:
                if not kspl.budget_id:
                    raise osv.except_osv("KDERP Warning",'Please input budget or unckeck Base On Line')
                    return False
        return True

    _constraints = [
        (_check_job_budget, 'Supplier Payment Job must be unique !',['payment_line','base_on_line']),
                    ]
    _defaults = {  
                'user_create_id':lambda obj,cr,uid,context: uid,
                'user_applicant_id':lambda obj,cr,uid,context: uid,
                'payment_type':_get_payment_type,
                'state': lambda *a: 'draft',
                'journal_id':_get_journal,
                'account_id':_get_default_account,
                'expense_account_id':_default_expense_account_id,
                'move_id':lambda *x: False,
                'tax_base':lambda *x:'p'
                }
    #Onchange
    def on_changevalue(self, cr, uid, ids, amount, adv, retention, taxes_id, type='amt',currency_id=False):
        subtotal=0
        subtotal=amount+adv+retention
        amount_tax=0
        if taxes_id[0][2]:
            tax_obj =self.pool.get('account.tax')
            
            val=0.0
            tax_brs = tax_obj.browse(cr, uid,taxes_id[0][2]) 
            for c in tax_obj.compute_all(cr, uid, tax_brs, amount, 1, False, False)['taxes']:
                val += c.get('amount', 0.0)
            
            if currency_id:
                cur_obj=self.pool.get('res.currency')
                cur_brs=cur_obj.browse(cr, uid, currency_id)
                amount_tax=cur_obj.round(cr, uid, cur_brs, val)
            else:
                amount_tax=val            
        result={'sub_total':subtotal,'amount_tax':amount_tax,'total':amount_tax+subtotal}
        return {'value':result}
    
    #Action
    def open_supplier_payment(self, cr, uid, ids, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": "Supplier Payment",
            "res_model": 'kderp.supplier.payment',
            "res_id": ids[0] if ids else False,
            "view_type": "form",
            "view_mode": "form",
            "target":"current",
            'context':context,
            'nodestroy': True,
            'domain': "[('id','in',%s)]" % ids
        }
    
    #Update Tax Line
    def compute(self, cr, uid, invoice_id, context=None):
        if not context: context={}
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        ksp = self.browse(cr, uid, invoice_id, context=context)
        exrate = context.get('new_exrate',0) if context.get('new_exrate',0)>0 else ksp.order_id.exrate 
        cur = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.currency_id
        ksp_cur=ksp.currency_id
        company_currency = cur.id
        
        supplier_code = " - " +  ksp.order_id.partner_id.code if ksp.order_id.partner_id.code else "None"
        
        if ksp.tax_base=='p':
                val_amount=ksp.amount
        elif ksp.tax_base=='p_adv':
            val_amount=ksp.advanced_amount
        elif ksp.tax_base=='p_retention':
            val_amount=ksp.retention_amount
        else:
            val_amount=ksp.amount + ksp.advanced_amount + ksp.retention_amount
        
        if val_amount:
            for tax in tax_obj.compute_all(cr, uid, ksp.taxes_id, val_amount, 1, False, False)['taxes']:
                val={}
                val['supplier_invoice_id'] = ksp.id
                val['name'] =  ksp.name +  supplier_code
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
    
                val['base_code_id'] = tax['base_code_id']
                val['tax_code_id'] = tax['tax_code_id']
                val['base_amount'] = val['base'] * tax['base_sign']*exrate
                val['tax_amount'] = val['amount'] * tax['tax_sign']*exrate
                val['account_id'] = tax['account_collected_id'] or False
                val['account_analytic_id'] = tax['account_analytic_collected_id']
    
                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'], val['name'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
        elif ksp.taxes_id:
            for tax in tax_obj.compute_all(cr, uid, ksp.taxes_id, val_amount, 1, False, False)['taxes']:
                val={}
                val['supplier_invoice_id'] = ksp.id
                val['name'] =  ksp.name +  supplier_code
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'])
    
                val['base_code_id'] = tax['base_code_id']
                val['tax_code_id'] = tax['tax_code_id']
                val['base_amount'] = val['base'] * tax['base_sign']*exrate
                val['tax_amount'] = val['amount'] * tax['tax_sign']*exrate
                val['account_id'] = tax['account_collected_id'] or False
                val['account_analytic_id'] = tax['account_analytic_collected_id']
    
                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'], val['name'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
            
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, ksp_cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, ksp_cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
    
    def update_supplier_taxes(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        ait_obj = self.pool.get('account.invoice.tax')
        for id in ids:
            cr.execute("DELETE FROM account_invoice_tax WHERE supplier_invoice_id=%s AND manual is False", (id,))
            for taxe in self.compute(cr, uid, id, ctx).values():
                ait_obj.create(cr, uid, taxe, ctx)
        return True
kderp_supplier_payment()

#Using when job rate is very very le
class kderp_supplier_payment_line(osv.osv):
    _name = 'kderp.supplier.payment.line'
    _description = 'Supplier Payment for Kinden'
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            ids = self.search(cr, user, [('account_analytic_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('budget_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                check=name.replace(',','')
                if check.isdigit():
                    ids = self.search(cr, user, [('amount','=',check)]+ args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    _columns={
              'base_on_line':fields.boolean('Base on Line'),
              'account_analytic_id':fields.many2one("account.analytic.account",'Job', required=True, ondelete="restrict"),
              'budget_id':fields.many2one("account.budget.post",'Budget', ondelete="restrict"),
              'amount':fields.float("Amount",required=True),
              'supplier_payment_id':fields.many2one('kderp.supplier.payment','Supplier Payment', ondelete='cascade'),
              }
    
    _sql_constraints = [('supplier_payment_detail_unique_no', 'unique(supplier_payment_id,account_analytic_id,budget_id)', 'Supplier Payment Job & Budget must be unique !')]
    
    _defaults={
               'amount':lambda *x: 0.0,
               'base_on_line':lambda obj,cr,uid,context: context.get('base_on_line',False),
               }
kderp_supplier_payment_line()


class account_invoice_tax(osv.osv):
    _name = "account.invoice.tax"
    _inherit="account.invoice.tax"
    
    _columns={
              'supplier_invoice_id': fields.many2one('kderp.supplier.payment', 'Supplier Invoice Line', ondelete='restrict', select=True),
              }
    
    def move_line_get_supplier_payment(self, cr, uid, ksp_id):
        res = []
        cr.execute("""SELECT
                        ait.* 
                    FROM
                        account_invoice_tax ait 
                     WHERE supplier_invoice_id=%s""", (ksp_id,))
        
        for t in cr.dictfetchall():
            if not t['amount'] \
                    and not t['tax_code_id'] \
                    and not t['tax_amount']:
                continue
            res.append({
                'type':'tax',
                'name':'VAT ' + t['name'],
                'price_unit': t['amount'],
                'quantity': 1,
                'price': t['amount'] or 0.0,
                'account_id': t['account_id'],
                'tax_code_id': t['tax_code_id'],
                'tax_amount': t['tax_amount'],
                'account_analytic_id': t['account_analytic_id'],
            })
        
        return res

account_invoice_tax()