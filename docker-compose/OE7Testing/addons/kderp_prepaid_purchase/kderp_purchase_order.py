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

from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp

import time
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import netsvc, SUPERUSER_ID

class purchase_order(osv.osv):
    """
        Add new field Purchase Order
    """
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'KDERP Purchase Order'

    def _get_summary_payment_amount(self, cr, uid, ids, name, args, context=None):#Tinh Requested Amount, Paid Amount, VAT Amount theo Currency Cua Purchase
        if not context: context={}
        res={}
        cur_obj = self.pool.get('res.currency')
        company_currency=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
                
        for po in self.browse(cr, uid, ids):            
            if po.allocate_order:
                if po.state not in ('draft','cancel'):                    
                    total_request_amount = po.amount_total
                    total_payment_amount = po.amount_total
                    total_vat_amount = po.amount_total
                    subtotal_vat_amount = po.final_price
                    amount_vat = po.amount_tax                    
                    payment_percentage = 1
                else:
                    total_request_amount = 0
                    total_payment_amount = 0
                    total_vat_amount = 0
                    subtotal_vat_amount = 0
                    amount_vat = 0
                    payment_percentage = 1
            else:
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
    
    def _get_order_from_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns={
                'allocate_order':fields.boolean("Allocate Order"),                               
                'total_request_amount':fields.function(_get_summary_payment_amount,string='Requested Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','state','state'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
                'total_vat_amount':fields.function(_get_summary_payment_amount,string='Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','state'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 25),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
                'subtotal_vat_amount':fields.function(_get_summary_payment_amount,string='Sub-Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','state'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 30),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
                'vat_amount':fields.function(_get_summary_payment_amount,string='VAT Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','state'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 30),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
                'total_payment_amount':fields.function(_get_summary_payment_amount,string='Payment Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','state'], 5),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['state','order_id'], 10),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
               
                'payment_percentage':fields.function(_get_summary_payment_amount,string='Payment Percentage',
                                                       method=True,type='float',multi="_get_summary",digits_compute=dp.get_precision('Percent'),
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','state','discount_amount','taxes_id'], 20),
                                                              'purchase.order.line': (_get_order_from_line, None, 10),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             })
              }
    _default = {
                'allocate_order': False,
                }

#Move to kderp_stock module    
#     def action_create_picking(self, cr, uid, ids, context = {}):
#         picking_id = self.action_picking_create(cr, uid, ids, context)
#         return picking_id    
#     
#     def action_cancel(self, cr, uid, ids, context=None):
#         res = super(purchase_order, self).action_cancel(cr, uid, ids, context)
#         wf_service = netsvc.LocalService("workflow")
#         for po in self.browse(cr, uid, ids):
#             for sp in po.picking_ids:
#                 if sp.state!='cancel':
#                     wf_service.trg_validate(uid, 'stock.picking', sp.id, 'button_cancel', cr)
#         return res
#         
#     def action_draft_to_final_quotation(self, cr, uid, ids, context=None):
#         if not context:
#             context = {}
#         todo = []
#         period_obj = self.pool.get('account.period')
#         picking_ids = []
#         for po in self.browse(cr, uid, ids, context=context):
#             if not po.order_line:
#                 raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
#             for line in po.order_line:
#                 if line.state=='draft':
#                     todo.append(line.id)
# 
#             period_id = po.period_id and po.period_id.id or False
#             if not period_id:
#                 period_ids = period_obj.find(cr, uid, po.date_order, context)
#                 period_id = period_ids and period_ids[0] or False
#             self.write(cr, uid, [po.id], {'state' : 'waiting_for_roa', 'period_id':period_id,'validator' : uid})
#                         
#             if po.allocate_order:
#                 sp_exists = False
#                 for sp in po.picking_ids:
#                     if sp.state!='cancel':
#                         sp_exists = True
#                         break
#                 if not sp_exists:
#                     picking_ids = self.action_create_picking(cr, uid, [po.id], context)
#         self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
#         return picking_ids
#     
#     def act_assign_move_picking(self, cr, uid, ids, context = {}):
#         todo_moves = []
#         stock_move = self.pool.get('stock.move')
#         wf_service = netsvc.LocalService("workflow")
#         for po in self.browse(cr, uid, ids, context):
#             for sp in po.picking_ids:
#                 if sp.state<>'cancel':
#                     for sm in sp.move_lines:
#                         todo_moves.append(sm.id)
#                     wf_service.trg_validate(uid, 'stock.picking', sp.id, 'button_confirm', cr)
#         stock_move.force_assign(cr, uid, todo_moves)
#         self.write(cr, uid, ids, {'state' : 'waiting_for_delivery'})        
#         return ids
#     
#     def action_receive_picking(self, cr, uid, ids, context = {}):
#         stock_move = self.pool.get('stock.move')                
#         for po in self.browse(cr, uid, ids, context):
#             for sp in po.picking_ids:
#                 todo_moves = []
#                 for sm in sp.move_lines:
#                     todo_moves.append(sm.id)
#                 stock_move.action_done(cr, uid, todo_moves)                
#         #self.write(cr, uid, ids, {'state' : 'done'})
#         return ids
#     
#     #Stock Picking and MoveArea
#     def date_to_datetime(self, cr, uid, userdate, context=None):
#         """ Convert date values expressed in user's timezone to
#         server-side UTC timestamp, assuming a default arbitrary
#         time of 12:00 AM - because a time is needed.
#     
#         :param str userdate: date string in in user time zone
#         :return: UTC datetime string for server-side use
#         """
#         from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
#         # TODO: move to fields.datetime in server after 7.0
#         user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
#         if context and context.get('tz'):
#             tz_name = context['tz']
#         else:
#             tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
#         if tz_name:
#             utc = pytz.timezone('UTC')
#             context_tz = pytz.timezone(tz_name)
#             user_datetime = user_date + relativedelta(hours=12.0)
#             local_timestamp = context_tz.localize(user_datetime, is_dst=False)
#             user_datetime = local_timestamp.astimezone(utc)
#             return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#         return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#     
#     def _prepare_order_picking(self, cr, uid, order, context=None):
#         return {
#             'name': self.pool.get('stock.picking').get_newcode(cr, uid, 'int', context),
#             'origin': order.name,
#             'date': self.date_to_datetime(cr, uid, order.date_order, context),
#             'partner_id': order.partner_id.id,
#             'invoice_state': 'none', 
#             'type': 'in',
#             'purchase_id': order.id,
#             #'company_id': order.company_id.id,
#             'move_lines' : [],
#         }
#     
#     def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
#         price_unit = order_line.price_unit
# #        if order.currency_id.id != order.company_id.currency_id.id:
#             #we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
# #            price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
#         return {
#             'name': order_line.name or '',
#             'product_id': order_line.product_id.id,
#             'product_qty': order_line.product_qty,
#             'product_uos_qty': order_line.product_qty,
#             'product_uom': order_line.product_uom.id,
#             'product_uos': order_line.product_uom.id,
#             'date': self.date_to_datetime(cr, uid, order.date_order, context),
#             #'date_expected': self.date_to_datetime(cr, uid, order_line.date_planned, context),
#             'location_id': order_line.location_id.id,
#             'location_dest_id': order_line.location_dest_id.id,
#             'picking_id': picking_id,
#             'partner_id': order.partner_id.id,
#             #'move_dest_id': order_line.move_dest_id.id,
#             'state': 'draft',
#             'type':'in',
#             'purchase_line_id': order_line.id,
#             #'company_id': order.company_id.id,
#             'price_unit': price_unit,
#             'source_move_code':order_line.move_code
#         }     
#     
#     def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
#         """Creates pickings and appropriate stock moves for given order lines, then
#         confirms the moves, makes them available, and confirms the picking.
# 
#         If ``picking_id`` is provided, the stock moves will be added to it, otherwise
#         a standard outgoing picking will be created to wrap the stock moves, as returned
#         by :meth:`~._prepare_order_picking`.
# 
#         Modules that wish to customize the procurements or partition the stock moves over
#         multiple stock pickings may override this method and call ``super()`` with
#         different subsets of ``order_lines`` and/or preset ``picking_id`` values.
# 
#         :param browse_record order: purchase order to which the order lines belong
#         :param list(browse_record) order_lines: purchase order line records for which picking
#                                                 and moves should be created.
#         :param int picking_id: optional ID of a stock picking to which the created stock moves
#                                will be added. A new picking will be created if omitted.
#         :return: list of IDs of pickings used/created for the given order lines (usually just one)
#         """
#         if not picking_id:
#             picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
#         todo_moves = []
#         stock_move = self.pool.get('stock.move')
#         wf_service = netsvc.LocalService("workflow")
#         for order_line in order_lines:
#             if not order_line.product_id:
#                 continue
#             if order_line.product_id.type in ('product', 'consu'):
#                 move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
#                 #if order_line.move_dest_id and order_line.move_dest_id.state != 'done':
#                 #    order_line.move_dest_id.write({'location_id': order.location_id.id})
#                 todo_moves.append(move)
#         stock_move.action_confirm(cr, uid, todo_moves)
#         return [picking_id]
# 
#     def action_picking_create(self, cr, uid, ids, context=None):
#         picking_ids = []
#         for order in self.browse(cr, uid, ids):
#             picking_ids.extend(self._create_pickings(cr, uid, order, order.order_line, None, context=context))
# 
#         # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
#         # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
#         # one that should trigger the advancement of the purchase workflow.
#         # By default we will consider the first one as most important, but this behavior can be overridden.
#         return picking_ids[0] if picking_ids else False
purchase_order()

class purchase_order_line(osv.osv):
    """
        Add new field link Prepaid Order to Purchase Order Line
    """
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'
    
    _columns = {
                'prepaid_purchase_order_line_id':fields.many2one('kderp.prepaid.purchase.order.line', 'Prepaid Order Line', ondelete='restrict'),
                'move_code':fields.integer('Move Code', readonly = 1),
#Move to kderp_stock module                
#                 'location_id':fields.many2one('stock.location', 'From Stock', readonly = 1),
#                 'location_dest_id':fields.many2one('stock.location', 'To Stock', readonly = 1),
                'move_ids':fields.one2many('stock.move','purchase_line_id','StockMoves')
                }
    
    def write(self, cr, uid, ids, vals, context = {}):
        res = super(purchase_order_line, self).write(cr, uid, ids, vals, context)
        if 'plan_qty' in vals or 'product_uom' in vals or 'product_id' in vals or 'name' in vals:
            todo_moves = {}
            for pol in self.browse(cr, uid, ids):
                if pol.order_id.allocate_order:
                    if 'name' in vals or 'product_id' in vals or 'product_uom' in vals:
                        raise osv.except_osv("KDVN Warning", "Can't change Product in Allocated Order")
                    elif pol.order_id.state not in ('draft','waiting_for_roa'):
                        raise osv.except_osv("KDVN Warning", "Can't change Allocated Order in this status")
                    val =  {}                    
                    for sm in filter(lambda move: move.state!='cancel' and pol.order_id.allocate_order and move.product_qty<>pol.plan_qty, pol.move_ids):
                        val={'product_qty':pol.plan_qty}                            
                        todo_moves[sm.id] = True
                        sm.write(val, context = context)
                            
                    check_error = self.pool.get('stock.location.product.detail').check_prepaid_product_availability(cr, uid, todo_moves.keys())
        return res