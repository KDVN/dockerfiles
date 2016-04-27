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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
#Add Job to Stock move using for Moving Expense
class StockMove(osv.osv):
    _inherit = 'stock.move'
    _name="stock.move"

    def _check_job_stock(self, cr, uid, ids, context=None):
        for sm in self.browse(cr, uid, ids):
            if sm.from_analytic_id and sm.location_id:
                job_source_ids = [job.id for job in sm.location_id.job_related_ids]
                if sm.from_analytic_id.id not in job_source_ids:
                    return False
            if sm.to_analytic_id and sm.location_dest_id:
                job_dest_ids = [job.id for job in sm.location_dest_id.job_related_ids]
                if sm.to_analytic_id.id not in job_dest_ids:
                    return False
        return True

    def _update_to_pol(self, cr, uid, ids, context=None):
        for sm in self.browse(cr, uid, ids):
            po_nos = []
            for pol in sm.pol_ids:
                if pol.order_id.state!='cancel':
                    po_nos.append(pol.order_id.name)
            if po_nos:
                raise osv.except_osv("KDERP Warning"," Can't change this Stock move, please check expense with number %s already confirm." % pol.order_id.name)
                return False
        return True

    def _get_subtotal(self, cr, uid, ids, name, args, context):
        res = {}
        for sm in self.browse(cr, uid, ids):
            res[sm.id] = sm.price_unit * sm.product_qty
        return res

    EXPENSE_STATES = (('pending','Pending'),
                     ('adjusted','Adjusted'))
    _columns ={
                'from_analytic_id':fields.many2one('account.analytic.account',"From Job", ondelete="restrict",help='Use for moving expense'),
                'to_analytic_id':fields.many2one('account.analytic.account',"To Job", ondelete="restrict", help='Use for moving expense'),
                'expense_state_in':fields.selection(EXPENSE_STATES,'Expense Status', readonly= 1, help='Pending: Expense not yet adjusted expense, Adjusted: Expenes already ajusted'),
                'expense_state_out':fields.selection(EXPENSE_STATES,'Expense Status', readonly= 1, help='Pending: Expense not yet adjusted expense, Adjusted: Expenes already ajusted'),
                'budget_id':fields.related('product_id','budget_id', string='Budget', type='many2one',relation='account.budget.post'),
                'price_unit': fields.float('Unit Price', digits_compute= dp.get_precision('Product Price'), readonly=True, states = {'draft': [('readonly', False)]}),
                'subtotal':fields.function(_get_subtotal, string='Sub-Total', type='float', digits_compute=dp.get_precision('Amount')),
                'pol_ids':fields.one2many('purchase.order.line','stock_move_id',"POL IDS",readonly=1)
                }
    _constraints = [(_check_job_stock, "KDERP Warning, Please check Warehouse and Job, job and warehouse must be related", ['from_analytic_id','to_analytic_id','location_id','location_dest_id']),
                    (_update_to_pol, "",['price_unit','product_id','product_qty','product_uom','from_analytic_id','to_analytic_id'])]
    _defaults = {
        'expense_state_out': 'pending',
        'expense_state_in': 'pending'
    }

    def move_expense(self, cr, uid, ids, context):
        context = context or {}
        job_id = context.get('job_id_move', False)
        exp_type = context.get('expense_type', False)
        po_obj = self.pool.get('purchase.order')
        partner_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.id
        new_po_id = False
        if job_id and exp_type:
            for sm in self.browse(cr, uid, ids, context):
                po_dict = {'date_order': sm.date}
                newCode = po_obj.new_code(cr, uid, [], job_id, 'I')
                po_dict['allocate_order'] = True
                po_dict['account_analytic_id'] = job_id
                po_dict['name'] = (newCode and newCode['value']['name'])
                po_dict['partner_id'] = partner_id
                po_dict['address_id'] = partner_id
                po_dict['taxes_id'] = []
                po_dict['notes'] = _("Moving expense from stock")
                po_dict['state'] = 'draft'
                pols = [(0, False, {'account_analytic_id':job_id,
                                        'product_id': sm.product_id.id,
                                        'product_uom': sm.product_uom.id,
                                        'plan_qty': sm.product_qty if exp_type=='in' else -sm.product_qty,
                                        'price_unit': sm.price_unit,
                                        'name': sm.name or sm.product_id.name,
                                        'stock_move_id': sm.id
                                        })]
                po_dict['order_line'] = pols
                new_po_id = po_obj.create(cr,uid, po_dict)
                po_obj.write(cr, uid, [new_po_id], {'state':'done'})
                #Remove workflow (don't use workflow in this case
                from openerp import netsvc
                wf_service = netsvc.LocalService("workflow")
                try:
                    wf_service.trg_delete(uid, 'purchase.order', new_po_id, cr)
                except:
                    continue
                expense_state = "expense_state_%s='adjusted'" % exp_type
                cr.execute("""Update stock_move set %s  where id=%d""" %(expense_state, sm.id))
        return new_po_id

    def revoke_expense(self, cr, uid, ids, context):
        context = context or {}
        pol_obj = self.pool.get('purchase.order.line')
        po_obj = self.pool.get('purchase.order')
        job_id = context.get('job_id_move', False)
        exp_type = context.get('expense_type', False)
        if job_id and exp_type:
            for sm in self.browse(cr, uid, ids, context):
                pol_ids = pol_obj.search(cr, uid, [('stock_move_id','=', sm.id),('product_id','=',sm.product_id.id),('account_analytic_id','=',job_id)])
                for pol in pol_obj.browse(cr, uid, pol_ids):
                    if pol.order_id.state!='cancel':
                        pol.order_id.write({'state':'cancel'})
                        from openerp import netsvc
                        wf_service = netsvc.LocalService("workflow")
                        try:
                            wf_service.trg_delete(uid, 'purchase.order', pol.order_id.id, cr)
                        except:
                            continue
                expense_state = "expense_state_%s='pending'" % exp_type
                cr.execute("""Update stock_move set %s where id=%d""" %(expense_state, sm.id))
        return True

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,
                            loc_dest_id=False, partner_id=False, context = {}):
        res = super(StockMove, self).onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id,
                            loc_dest_id=loc_dest_id, partner_id=partner_id)
        context = context or {}
        if 'value' in res and prod_id and context.get('get_price', False):
            company_obj = self.pool.get('res.users').browse(cr, uid, uid).company_id
            cur_obj = self.pool.get('res.currency')
            cur_obj_id = company_obj.currency_id
            diffPercent = company_obj.stock_price_different
            field_to_read = company_obj.stock_baseon_typeprice
            remainPercent = 1 + diffPercent/100.0
            getPrice = self.pool.get('product.product').read(cr, uid, prod_id, [field_to_read])[field_to_read]
            res['value']['price_unit'] = cur_obj.round(cr, uid, cur_obj_id, getPrice* remainPercent)
        return res

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        for move in self.browse(cr, uid, ids, context=context):
            if move.state!='draft' or move.expense_state_in != 'pending' or move.expense_state_out != 'pending':
                raise osv.except_osv(_('KDERP User Error!'), _('You can only delete draft or not Adjusted expense moves.'))
        return super(StockMove, self).unlink( cr, uid, ids, context=ctx)