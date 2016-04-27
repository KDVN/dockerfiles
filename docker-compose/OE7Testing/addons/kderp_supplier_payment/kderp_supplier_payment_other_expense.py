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
    
class kderp_supplier_payment_expense(osv.osv):
    _name = 'kderp.supplier.payment.expense'
    _description = 'Supplier Payment for Expense'

    #SYSTEM METHOD
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name',operator,name.strip())]+ args, limit=limit, context=context)
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
    
    def write(self, cr, uid, ids, vals, context={}):
        if vals:
            if len(ids)>0 and 'date_bc_to_acc' in context and 'bc_to_accounting_date' not in vals:
                if context.get('date_bc_to_acc',False):
                    vals['bc_to_accounting_date']=context['date_bc_to_acc']
        if 'wkf' in context:
            for kspe in self.browse(cr, uid, ids,context):
                new_val = vals
                if kspe.bc_to_accounting_date:
                    if  'bc_to_accounting_date' in new_val:
                        pop_date = new_val.pop('bc_to_accounting_date')
                osv.osv.write(self, cr, uid, [kspe.id],new_val,context=context)
        else:
            osv.osv.write(self, cr, uid, ids, vals, context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return True
    
    def create(self, cr, uid, vals, context={}):
        res=osv.osv.create(self, cr, uid, vals, context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return res
    
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
        return super(kderp_supplier_payment_expense, self).copy(cr, uid, id, default, context)
    
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

        kspe = self.browse(cr, uid, invoice_id, context=context)
        exrate = context.get('new_exrate',0) if context.get('new_exrate',0)>0 else kspe.exrate 
        company_currency = self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id.id
        if kspe.payment_line:
            for kspl in kspe.payment_line:
                mres ={
                        'type':'src',
                        'name':kspe.name,
                        'price_unit':kspl.amount,
                        'quantity':1,
                        'price':kspl.amount,
                        'account_id':kspe.expense_account_id.id,
                        'product_id':False,
                        'uos_id':False,
                        'account_analytic_id':kspl.account_analytic_id.id,
                        'taxes':False}
                if not mres:
                    continue
                res.append(mres)
                tax_code_found= False
                payment_per_vat = kspl.amount/kspe.amount if kspe.amount else 0
                if payment_per_vat:
                    for tax in tax_obj.compute_all(cr, uid, kspe.taxes_id,kspl.amount,
                            1, False,
                            False)['taxes']:            
                        tax_code_id = tax['base_code_id']
                        tax_amount = (kspl.amount*payment_per_vat * tax['base_sign'])
        
                        if tax_code_found:
                            if not tax_code_id:
                                continue
                            res.append({
                                        'type':'src',
                                        'name':kspe.name,
                                        'price_unit':kspl.amount,
                                        'quantity':1,
                                        'price':kspl.amount,
                                        'account_id':kspe.expense_account_id.id,
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
                elif (payment_per_vat==0 and kspe.taxes_id):
                    amount_tax=0.0
                    for tax in tax_obj.compute_all(cr, uid, kspe.taxes_id,1,
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
                                        'name':kspe.name,
                                        'price_unit':0,
                                        'quantity':1,
                                        'price':kspl.amount,
                                        'account_id':kspe.expense_account_id.id,
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
        elif kspe.taxes_id:
            amount_tax=0.0
            tax_code_found= False
            res.append({
                        'type':'src',
                        'name':kspe.name,
                        'price_unit':0,
                        'quantity':1,
                        'price':0,
                        'account_id':kspe.expense_account_id.id,
                        'product_id':False,
                        'uos_id':False,
                        'account_analytic_id':False,
                        'taxes':False})
            for tax in tax_obj.compute_all(cr, uid, kspe.taxes_id,1,
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
                               'name':kspe.name,
                               'price_unit':0,
                               'quantity':1,
                               'price':0,
                               'account_id':kspe.expense_account_id.id,
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
        elif kspe.expense_id.expense_line:
            payment_per = kspe.amount/kspe.expense_id.amount_untaxed if kspe.expense_id.amount_untaxed else 0 #Tinh % 1 payment amount /po amount
            payment_per_vat = kspe.amount/kspe.expense_id.amount_untaxed if kspe.expense_id.amount_untaxed else 0
            cr.execute("""Select 
                                account_analytic_id,
                                sum(coalesce(amount,0)) 
                            from 
                                kderp_other_expense_line where expense_id in (%s) group by account_analytic_id""" % (kspe.expense_id.id))
            for aaa_id,amount in cr.fetchall():
                mres ={
                        'type':'src',
                        'name':kspe.name,
                        'price_unit':amount*payment_per,
                        'quantity':1,
                        'price':amount*payment_per,
                        'account_id':kspe.expense_account_id.id,
                        'product_id':False,
                        'uos_id':False,
                        'account_analytic_id':aaa_id,
                        'taxes':False}
                if not mres:
                    continue
                res.append(mres)
                tax_code_found= False

                if payment_per_vat>0:
                    for tax in tax_obj.compute_all(cr, uid, kspe.taxes_id,amount*payment_per,
                            1, False,
                            False)['taxes']:            
                        tax_code_id = tax['base_code_id']
                        tax_amount = (payment_per_vat*amount * tax['base_sign'])
        
                        if tax_code_found:
                            if not tax_code_id:
                                continue
                            res.append({
                                        'type':'src',
                                        'name':kspe.name,
                                        'price_unit':amount*payment_per,
                                        'quantity':1,
                                        'price':amount*payment_per,
                                        'account_id':kspe.expense_account_id.id,
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
        kspe = self.browse(cr, uid, id)
        cur_obj = self.pool.get('res.currency')
        exrate = context.get('exrate',0) if context.get('exrate',0) else kspe.exrate
        company_currency = self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id.id

        sign = -1

        iml = self.move_line_get(cr, uid, kspe.id, context=context)
        
        for il in iml:
            if il['account_analytic_id']:
                ref = kspe.name
                if not kspe.journal_id.analytic_journal_id:
                    raise osv.except_osv(_('No Analytic Journal!'),_("You have to define an analytic journal on the '%s' journal!") % (kspe.journal_id.name,))
                il['analytic_lines'] = [(0,0, {
                    'name': il['name'],
                    'date': kspe.date,
                    'account_id': il['account_analytic_id'],
                    'unit_amount': il['quantity'],
                    'amount':  cur_obj.round(cr, uid,self.pool['res.users'].browse(cr, uid, uid).company_id.currency_id , il['price']*exrate)*sign,
                    'product_id': il['product_id'],
                    'product_uom_id': il['uos_id'],
                    'general_account_id': il['account_id'],
                    'journal_id': kspe.journal_id.analytic_journal_id.id,
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

        vat = self.update_supplier_expense_taxes(cr, uid, ids, context)
        
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        
    #    payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        company =  self.pool['res.users'].browse(cr, uid, uid).company_id

        for kspe in self.browse(cr, uid, ids, context=context):

            exrate = context.get('new_exrate',0) if context.get('new_exrate',0)>0 else kspe.exrate
            if not kspe.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if kspe.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': kspe.expense_id.partner_id.lang})
            #if not kspe.date:
             #   self.write(cr, uid, [kspe.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = company.currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, kspe.id, context=ctx)
   
            # one move line per tax line
            iml += ait_obj.move_line_get_supplier_payment_expense(cr, uid, kspe.id)
            #raise osv.except_osv("EEEEEEEEEEEE", ait_obj.move_line_get_supplier_payment(cr, uid, kspe.id))
            entry_type = ''
            ref = kspe.name
            entry_type = 'journal_pur_voucher'

            diff_currency_p = kspe.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, kspe, company_currency, ref, iml, context=ctx)
            acc_id = kspe.account_id.id
            #raise osv.except_osv("EEEEEEFF",iml)
            name = kspe.name
            totlines = False
            
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': kspe.date})
                for t in totlines:
                    if kspe.currency_id.id != company_currency:
                        amount_currency = cur_obj.round(cr, uid, company.currency_id,t[1]/exrate) if exrate else 0  #cur_obj.compute(cr, uid, company_currency, kspe.currency_id.id, t[1], context=ctx)
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
                    'date_maturity': kspe.due_date or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and kspe.currency_id.id or False,
                    'ref': ref
            })
            
            date = kspe.date or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(kspe.expense_id.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, kspe)
            
            journal_id = kspe.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, kspe, line)
            
            move = {
                'ref': kspe.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': kspe.description,
                'company_id': company.id,
            }
            period_id = kspe.period_id and kspe.period_id.id or False
            ctx.update(company_id=company.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, kspe.date, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
                    
            ctx.update(invoice=kspe)
            
            #raise osv.except_osv("E",move)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            #raise osv.except_osv("E",move)
        
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            #raise osv.except_osv("E",move)
            # make the invoice point to that move
            self.write(cr, uid, [kspe.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post_supplier(cr, uid, [move_id], context=ctx)
        
        return True
    
    def check_and_reconcile(self, cr, uid, ids, *args):
        kp_obj = self.pool.get('kderp.supplier.payment.expense.pay')
        for kspe in self.browse(cr, uid, ids):
            must_run =False
            kp_ids = []
            for kp in kspe.payment_ids:
                must_run = True
                kp_ids.append(kp.id)
            if must_run:
                kp_obj.action_reconcile(cr, uid, kp_ids, context={})
        return True
    
    def btn_action_revising_completed(self, cr, uid, ids, context):
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
        vat_invoices=self.read(cr, uid, ids,['kderp_vat_invoice_ids'])

        for vi in vat_invoices:
            if vi['kderp_vat_invoice_ids']:
                self.pool.get('kderp.supplier.vat.invoice').write(cr, uid, vi['kderp_vat_invoice_ids'],{'state':'draft'})
                
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])

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
        return True    
    
    def wkf_action_payment_done(self, cr, uid, ids, *args):
        list=[]
        for kspe in self.browse(cr, uid, ids):
            if kspe.payment_type=='na':
                list.append(str(kspe.name))                
        if list: raise osv.except_osv("KDERP Warning","Please choose Payment type before submit ! %s " % list)
        ctx={'date_bc_to_acc': time.strftime('%Y-%m-%d'),'wkf':True}
        self.write(cr,uid,ids,{'state':'completed'},context=ctx)
        return True
    
    def wkf_action_cancel_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            wf_service.trg_create(uid, 'kderp.supplier.payment.expense', inv_id, cr)
        return True
    
    #METHOD FOR FIELD FUNCTION    
#     def _compute_lines(self, cr, uid, ids, name, args, context=None):
#         result = {}
#         for kspe in self.browse(cr, uid, ids, context=context):
#             src = []
#             lines = []
#             if kspe.move_id:
#                 for m in kspe.move_id.line_id:
#                     temp_lines = []
#                     if m.reconcile_id:
#                         temp_lines = map(lambda x: x.id, m.reconcile_id.line_id)
#                     elif m.reconcile_partial_id:
#                         temp_lines = map(lambda x: x.id, m.reconcile_partial_id.line_partial_ids)
#                     lines += [x for x in temp_lines if x not in lines]
#                     src.append(m.id)
# 
#             lines = filter(lambda x: x not in src, lines)
#             result[kspe.id] = lines
#         return result

    def _get_payment_expense_from_line(self, cr, uid, ids, context=None):
        res={}
        for kspel in self.pool.get('kderp.supplier.payment.expense.line').browse(cr, uid, ids):
            res[kspel.supplier_payment_expense_id.id] =True
        return res.keys()
    
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
    
    def _get_summary_amount(self, cr, uid, ids, name, args, context={}):
        res={}
        tax_obj =self.pool.get('account.tax')
        cur_obj=self.pool.get('res.currency')
        for kspe in self.browse(cr, uid, ids,context):
            amount=0
            for kspel in kspe.payment_line:
                amount+=kspel.amount
            amount_tax=0
            if kspe.taxes_id:
                val=0.0
                for c in tax_obj.compute_all(cr, uid, kspe.taxes_id, amount, 1, False, False)['taxes']:
                    val += c.get('amount', 0.0)
                
                amount_tax=cur_obj.round(cr, uid, kspe.currency_id, val) if kspe.currency_id else val
                
            res[kspe.id]={'amount':amount,
                          'amount_tax':amount_tax,
                        'total': amount  + amount_tax }
        return res
    
    def _get_sno_year(self, cr, uid, ids, name, args, context={}):
        res = {}
        for kspe in self.browse(cr, uid, ids, context):
            try:
                sno=int(kspe.name[5:])
            except:
                sno=0
            try:
                year=kspe.name[:4][2:]
            except:
                year=""
            
            res[kspe.id]={'number': sno,'year': year}
            
        return res
    
    def _get_exrate(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        company_currency = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
        company_currency=company_currency.id
        res = {}
        for rope in self.browse(cr,uid,ids):
            from_curr = rope.currency_id.id
            compute_date = rope.expense_id.date
            res[rope.id] = cur_obj.compute(cr, uid, from_curr, company_currency, 1, round=False,context={'date': compute_date})
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
                                kderp_supplier_payment_expense.name AS code
                            FROM 
                                kderp_supplier_payment_expense
                            WHERE
                                length(kderp_supplier_payment_expense.name::text)=
                                ((SELECT 
                                length(prefix || suffix) + padding AS length
                                FROM 
                                ir_sequence
                                WHERE 
                                ir_sequence.code::text = 'kderp_supplier_payment_code_ot'::text LIMIT 1))
                            ) cnewcode ON cnewcode.code::text ~~ (isq.prefix || to_char(DATE '%s',  suffix || lpad('_',padding,'_')))
                            WHERE isq.code::text = 'kderp_supplier_payment_code_ot'::text AND isq.active) wnewcode
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
#     def _get_payment_type(self, cr, uid, context={}):
#         if not context:
#             context={}
#         cr.execute("""SELECT uid
#                               FROM res_groups_users_rel 
#                                   where gid in( select id from res_groups where name ='KDERP - Supplier Payment Expense Read Only Bankstransfer')
#                             and uid =%s
#                             """%(uid))
#         if cr.rowcount !=0:  
#             payment_type='cash'     
#         else:
#             payment_type='na'   
#         return payment_type
#     
    _order='year desc, number desc, name desc'
    _columns={
              #Code Filed Area
              'name':fields.char('R.O.P. No.',size=25,states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              
              'number':fields.function(_get_sno_year,type='integer',method=True,string='No.',multi='_get_sno_year',
                                       store={'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['name'], 10)}),
                                                 
              'year':fields.function(_get_sno_year,string='Year',method=True,type='char',size=4,multi='_get_sno_year',
                                     store={'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['name'], 10)}),
              
              'payee':fields.char('Payee',size=64),
              
              'payment_type':fields.selection([('bank','Bankstransfer'),('cash','By Cash'),('na','Not Available')],'Payment type',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]},required=True),

              'description':fields.text('Description',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              'date':fields.date('R.O.P. Date',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              
              'due_date':fields.date('Due Date',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),

              'amount':fields.function(_get_summary_amount,string='Amount',digits_compute=dp.get_precision('Amount'),
                                   method=True,type='float',size=4,multi='_get_summary_amount',
                                  store={'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['amount','taxes_id','currency_id'], 10),
                                          'kderp.supplier.payment.expense.line': (_get_payment_expense_from_line, None, 10)}),
              
              'exrate':fields.function(_get_exrate,type='float',method=True,string='Ex.Rate',
                                       store={'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['date','currency_id','expense_id'], 10)}),

              'amount_tax':fields.function(_get_summary_amount,string='VAT Amt',digits_compute=dp.get_precision('Amount'),
                                   method=True,type='float',size=4,multi='_get_summary_amount',
                                  store={'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['amount','taxes_id','currency_id'], 5),
                                          'kderp.supplier.payment.expense.line': (_get_payment_expense_from_line, None, 10)}),
              
              'total':fields.function(_get_summary_amount,string='Total',digits_compute=dp.get_precision('Amount'),
                                   method=True,type='float',size=4,multi='_get_summary_amount',
                                   store={'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['amount','taxes_id','currency_id'], 10),
                                          'kderp.supplier.payment.expense.line': (_get_payment_expense_from_line, None, 10)}),
              
              'amount_to_word_vnd':fields.function(_amount_to_word,string='In VND',method=True,type='char',size=1000,multi="_get_multi_to_word",
                                                   store={
                                                          'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['amount','taxes_id','currency_id'], 15),
                                                          'kderp.supplier.payment.expense.line': (_get_payment_expense_from_line, None, 15)}),
              'amount_to_word_usd':fields.function(_amount_to_word,string='In USD',method=True,type='char',size=1000,multi="_get_multi_to_word",
                                                    store={
                                                          'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['amount','taxes_id','currency_id'], 15),
                                                          'kderp.supplier.payment.expense.line': (_get_payment_expense_from_line, None, 15)}),
              
              'bc_to_accounting_date':fields.date('Date B.C. to Acc.',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]},help='This date is Budget Control sent to Accouting for Payment to supplier'),
              
              'move_name': fields.char('Journal Entry', size=64, readonly=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
          
              'state': fields.selection([
                                        ('draft','Draft'),
                                        ('waiting_bod','BOD checking'),#Waiting for B.O.D. confirmation->BOD Checking
                                        ('completed','BOD approved'), #BOD approved->Completed
                                        ('revising','Revising'),
                                        ('paid','Paid'),
                                        ('done','Paid'),
                                        ('cancel','Rejected')],'State', select=True, readonly=True),
              #Relation Field
              'supplier_id': fields.related('expense_id', 'partner_id', type='many2one',relation='res.partner', string='Supplier',readonly=True,store=True),              
              #Accounting
              'account_id': fields.many2one('account.account', 'Account', required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}, help="The partner account used for this invoice."),
              'move_id': fields.many2one('account.move', 'Detail', readonly=True, select=1,ondelete='restrict'),
              'journal_id': fields.many2one('account.journal', 'Journal', required=True, states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]},domain=[('type','=','purchase')]),              
              'expense_account_id': fields.many2one('account.account', 'Expense Acc.', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')], help="Expense account related to the selected product.",states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True, states={'draft':[('readonly',False)]}),
              
              'currency_id':fields.many2one('res.currency','Currency',required=True,states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              
              'user_create_id':fields.many2one("res.users","Create User"),
              'expense_id':fields.many2one('kderp.other.expense','Expense No.',required=True,states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              'user_applicant_id':fields.many2one('res.users','Applicant User',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              
              'taxes_id': fields.many2many('account.tax', 'supplier_payment_expense_tax', 'supplier_payment_expense_id', 'tax_id', 'Taxes', states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              'kderp_vat_invoice_ids':fields.many2many('kderp.supplier.vat.invoice','kderp_supplier_payment_expense_vat_invoice_rel', 'payment_expense_id', 'vat_invoice_id', 'VAT Invoices',states={'cancel':[('readonly',True)]},ondelete='restrict'),
              
#              'payment_ids': fields.function(_compute_lines, relation='account.move.line', type="many2many", string='Payments'),
              
              'payment_line':fields.one2many('kderp.supplier.payment.expense.line','supplier_payment_expense_id','Detail of payemnt',states={'cancel':[('readonly',True)],'paid':[('readonly',True)],'completed':[('readonly',True)]}),
              'tax_line_ids': fields.one2many('account.invoice.tax', 'supplier_payment_expense_id', 'Tax Lines', readonly=True, states={'draft':[('readonly',False)]}),
              }
    _sql_constraints = [('supplier_payment_expense_unique_no', 'unique(name)', 'Supplier Payment Number must be unique !')]
    
    _defaults = {  
                'user_create_id':lambda obj,cr,uid,context: uid, 
                'state': lambda *a: 'draft',
                'journal_id':_get_journal,
                'account_id':_get_default_account,
                'expense_account_id':_default_expense_account_id,
                'move_id':lambda *x: False,
                'payment_type':lambda *a: 'na'
                }
    #Onchange
    def on_changevalue(self, cr, uid, ids, amount, taxes_id, type='amt',currency_id=False):
        subtotal=0
        subtotal=amount
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
        result={'amount_tax':amount_tax,'total':amount_tax+subtotal}
        return {'value':result}
    
    #Action
    def open_expense_supplier_payment(self, cr, uid, ids, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": "Supplier Payment",
            "res_model": 'kderp.supplier.payment.expense',
            "res_id": ids[0] if ids else False,
            "view_type": "form",
            "view_mode": 'form,tree',
            'context':context,
            "target":"current",
            'nodestroy': True,
            'domain': "[('id','in',%s)]" % ids
        }
            
    #Update Tax Line
    def compute(self, cr, uid, invoice_id, context=None):
        if not context: context={}
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        kspe = self.browse(cr, uid, invoice_id, context=context)
        exrate = context.get('new_exrate',0) if context.get('new_exrate',0)>0 else kspe.exrate 
        cur = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.currency_id
        kspe_cur = kspe.currency_id
        company_currency = cur.id
        
        supplier_code = " - " +  kspe.expense_id.partner_id.code
        if kspe.taxes_id:
            for tax in tax_obj.compute_all(cr, uid, kspe.taxes_id, kspe.amount, 1, False, False)['taxes']:
                val={}
                val['supplier_payment_expense_id'] = kspe.id
                val['name'] =  kspe.name +  supplier_code
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
            t['base'] = cur_obj.round(cr, uid, kspe_cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, kspe_cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped
    
    def update_supplier_expense_taxes(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        ait_obj = self.pool.get('account.invoice.tax')
        for id in ids:
            cr.execute("DELETE FROM account_invoice_tax WHERE supplier_payment_expense_id=%s AND manual is False", (id,))
            for taxe in self.compute(cr, uid, id, ctx).values():
                ait_obj.create(cr, uid, taxe, ctx)
        return True
kderp_supplier_payment_expense()

#Using when job rate is very very le
class kderp_supplier_payment_line_other_expense(osv.osv):
    _name = 'kderp.supplier.payment.expense.line'
    _description = 'Supplier Payment Line for Expense'
    
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
                    ids = self.search(cr, user, [('amount','=',check)]+ args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    _columns={
              'account_analytic_id':fields.many2one("account.analytic.account",'Job', required=True, ondelete="restrict"),
              'amount':fields.float("Amount",required=True),
              'supplier_payment_expense_id':fields.many2one('kderp.supplier.payment.expense','Supplier Payment',required=True,ondelete='cascade'),
              }
    _defaults={
               'amount':lambda *x: 0.0
               }
    _sql_constraints = [('supplier_payment_exp_detail_unique_no', 'unique(supplier_payment_expense_id, account_analytic_id)', 'Supplier Payment Expense Job must be unique !')]
kderp_supplier_payment_line_other_expense()


class account_invoice_tax(osv.osv):
    _name = "account.invoice.tax"
    _inherit="account.invoice.tax"
    
    _columns={
              'supplier_payment_expense_id': fields.many2one('kderp.supplier.payment.expense', 'Supplier Payment Expense Line', ondelete='restrict', select=True),
              }
    
    def move_line_get_supplier_payment_expense(self, cr, uid, kspe_id):
        res = []
        cr.execute("""SELECT
                        ait.* 
                    FROM
                        account_invoice_tax ait 
                     WHERE supplier_payment_expense_id=%s""", (kspe_id,))
        
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