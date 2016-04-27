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

from openerp.osv import fields, osv

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import netsvc, SUPERUSER_ID
from openerp.tools.translate import _

import time
import pytz

# TODO: Need change when 
class purchase_order(osv.osv):
    """
        Add new field Purchase Order
    """
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'KDERP Purchase Order'

    def _get_move_ids(self, cr, uid, ids, name, args, context):
        res={}
        for po in self.browse(cr, uid, ids):
            sm_ids = {}
            for sp in po.picking_ids:
                for sm in sp.move_lines:
                    sm_ids[sm.id] = True
            res[po.id] = sm_ids.keys()
        return res

    #Fill source_location when partner is supplier
    def _get_from_location(self, cr, uid, context):
        domain = [('usage','=','supplier')]
        stock_supplier_ids = self.pool.get('stock.location').search(cr, uid, domain)
        return stock_supplier_ids and stock_supplier_ids[0]

    _columns = {
                'picking_ids': fields.one2many('stock.picking', 'purchase_id', 'Picking List', readonly=True, help="This is the list of incoming shipments that have been generated for this purchase order."),
                'received_details':fields.function(_get_move_ids,
                                                   type='one2many',
                                                   relation='stock.move',
                                                   string='Detail Moves'),
                'source_location_id':fields.many2one('stock.location','From Stock', domain = [('usage','=','supplier',),('global_stock','=',True)],
                                                                                    ondelete='restrict', 
                                                                                    states={'done':[('readonly',True)], 'cancel':[('readonly',True)]})
                }
    _defaults = {
                'source_location_id':_get_from_location
    }
    def action_create_picking(self, cr, uid, ids, context = {}):
        picking_id = self.action_picking_create(cr, uid, ids, context)
        return picking_id    
    
    def action_cancel(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).action_cancel(cr, uid, ids, context)
        wf_service = netsvc.LocalService("workflow")
        for po in self.browse(cr, uid, ids):
            for sp in po.picking_ids:
                if sp.state!='cancel':
                    wf_service.trg_validate(uid, 'stock.picking', sp.id, 'button_cancel', cr)
        return res
    
    def action_create_packing(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        todo = []
        picking_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)
                                        
            sp_exists = False
            for sp in po.picking_ids:
                if sp.state!='cancel':
                    sp_exists = True
                    break
            if not sp_exists:
                picking_ids = self.action_create_picking(cr, uid, [po.id], context)
                
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        return picking_ids
    
    def action_draft_to_final_quotation(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        
        period_obj = self.pool.get('account.period')
        
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))           

            period_id = po.period_id and po.period_id.id or False
            if not period_id:
                period_ids = period_obj.find(cr, uid, po.date_order, context)
                period_id = period_ids and period_ids[0] or False
            self.write(cr, uid, [po.id], {'state' : 'waiting_for_roa', 'period_id':period_id,'validator' : uid})

        res = self.action_create_packing(cr, uid, ids, context)

        # #Confirm Packing and Move
        # wf_service = netsvc.LocalService("workflow")
        # stock_move = self.pool.get('stock.move')
        # todo_moves = []
        # sp_obj = res and self.pool.get('stock.picking').browse(cr, uid, res)
        # if sp_obj and sp_obj.state<>'cancel':
        #     for sm in sp_obj .move_lines:
        #         todo_moves.append(sm.id)
        #     # wf_service.trg_validate(uid, 'stock.picking', sp_obj.id, 'button_confirm', cr)
        # stock_move.action_confirm(cr, uid, todo_moves)
        return res
    
    def act_assign_move_picking(self, cr, uid, ids, context = {}):
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        self.write(cr, uid, ids, {'state' : 'waiting_for_delivery'})
        for po in self.browse(cr, uid, ids, context):
            for sp in po.picking_ids:
                if sp.state<>'cancel':
                    for sm in sp.move_lines:
                        todo_moves.append(sm.id)
                    wf_service.trg_validate(uid, 'stock.picking', sp.id, 'button_confirm', cr)
        stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)
        return ids
    
    def action_receive_picking(self, cr, uid, ids, context = {}):
        stock_move = self.pool.get('stock.move')                
        for po in self.browse(cr, uid, ids, context):
            for sp in po.picking_ids:
                todo_moves = []
                for sm in sp.move_lines:
                    todo_moves.append(sm.id)
                stock_move.action_done(cr, uid, todo_moves)                
        self.write(cr, uid, ids, {'state' : 'waiting_for_payment'})
        return ids
    
    #Stock Picking and MoveArea
    def date_to_datetime(self, cr, uid, userdate, context=None):
        """ Convert date values expressed in user's timezone to
        server-side UTC timestamp, assuming a default arbitrary
        time of 12:00 AM - because a time is needed.
    
        :param str userdate: date string in in user time zone
        :return: UTC datetime string for server-side use
        """
        from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
        # TODO: move to fields.datetime in server after 7.0
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
        if context and context.get('tz'):
            tz_name = context['tz']
        else:
            tz_name = self.pool.get('res.users').read(cr, SUPERUSER_ID, uid, ['tz'])['tz']
        if tz_name:
            utc = pytz.timezone('UTC')
            context_tz = pytz.timezone(tz_name)
            user_datetime = user_date + relativedelta(hours=12.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    
    def _prepare_order_picking(self, cr, uid, order, context=None, type='in'):
        return {
            'name': self.pool.get('stock.picking').get_newcode(cr, uid, type, context),
            'origin': order.origin,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'partner_id': order.partner_id.id,
            'invoice_state': 'none', 
            'type': 'in',
            'purchase_id': order.id,
            #'company_id': order.company_id.id,
            'move_lines' : [],
            'location_id': order.source_location_id and order.source_location_id.id,
            'location_dest_id': order.location_id and order.location_id.id,
            'storekeeper_incharge_id': order.receiver_id and order.receiver_id.id
        }
    
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None, type = type):
        price_unit = order_line.price_unit
#        if order.currency_id.id != order.company_id.currency_id.id:
            #we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
#            price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
        error = ""
        if self.has_stockable_product(cr, uid, [order.id], context) and ((not order_line.location_id and not order.source_location_id) or  (not order_line.location_dest_id and not order.location_id)):             
                error = _("""Not Available From Stock or To Stock, could you please check""")
        if error:
            raise osv.except_osv(_("KDERP Warning"), error)
        
        return {
            'name': order_line.name or '',
            'product_id': order_line.product_id.id,
            'product_qty': order_line.product_qty,
            'product_uos_qty': order_line.product_qty,
            'product_uom': order_line.product_uom.id,
            'product_uos': order_line.product_uom.id,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            #'date_expected': self.date_to_datetime(cr, uid, order_line.date_planned, context),
            'location_id': order_line.location_id.id if order_line.location_id else order.source_location_id.id,
            'location_dest_id': order_line.location_dest_id.id if order_line.location_dest_id else order.location_id.id,
            'picking_id': picking_id,
            'partner_id': order.partner_id.id,
            #'move_dest_id': order_line.move_dest_id.id,
            'state': 'draft',
            'type':'in',
            'purchase_line_id': order_line.id,
            #'company_id': order.company_id.id,
            'price_unit': price_unit,
            'source_move_code':order_line.move_code
        }     
    
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Creates pickings and appropriate stock moves for given order lines, then
        confirms the moves, makes them available, and confirms the picking.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: purchase order to which the order lines belong
        :param list(browse_record) order_lines: purchase order line records for which picking
                                                and moves should be created.
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if omitted.
        :return: list of IDs of pickings used/created for the given order lines (usually just one)
        """
        type = 'in'
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context, type = type))
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
            if order_line.product_id.type in ('product', 'consu'):
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context, type = type))
                #if order_line.move_dest_id and order_line.move_dest_id.state != 'done':
                #    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        return [picking_id]

    def action_picking_create(self, cr, uid, ids, context=None):
        picking_ids = []
        #Ignore create packing if all products is service
        if self.has_stockable_product(cr, uid, ids):
            for order in self.browse(cr, uid, ids):
                picking_ids.extend(self._create_pickings(cr, uid, order, order.order_line, None, context=context))
    
            # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
            # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
            # one that should trigger the advancement of the purchase workflow.
            # By default we will consider the first one as most important, but this behavior can be overridden.
        return picking_ids[0] if picking_ids else False
    
    def has_stockable_product(self, cr, uid, ids, *args):
        for order in self.browse(cr, uid, ids):
            for order_line in order.order_line:
                if order_line.product_id and order_line.product_id.type in ('product', 'consu'):
                    return True
        return False
    
    def check_product_shipped(self, cr, uid, ids, *args):
        res = True
        for order in self.browse(cr, uid, ids):
            for pol in order.order_line:
                if pol.product_qty != pol.received_qty or not pol.received_qty:
                    return False
        return res
    
    def get_po_ids(self, cr, uid, ids, *args):
        return ids
    
    #Return PO ID for Trigger Workflow
    def get_po_from_stock_move_ids(self, cr, uid, ids, *args):
        sm_ids = []
        for po in self.browse(cr, uid, ids):
            for pol in po.order_line:
                for sm in pol.move_ids:
                    sm_ids.append(sm.id)                    
        return list(set(sm_ids))
    
purchase_order()

class purchase_order_line(osv.osv):
    """
        Add new field link Purchase Order Line
    """
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'
    
    def _get_product_received_qty(self, cr, uid, ids, fileds, arg, context=None):
        res = {}
        pol_list=[]
        #TODO: Later If using convert product unit must convert this one too
        for pol in self.browse(cr, uid, ids, context=context):
            if pol.product_id.type in ('product', 'consu'):
                ################
                #Later Get from Stock Move 
                #################
                pol_list.append(pol.id)
                res[pol.id]=0
            else:
                res[pol.id] = pol.plan_qty
        if pol_list:                
            pol_ids=",".join(map(str,pol_list))
            cr.execute("""select 
                            pol.id,
                            sum(coalesce(sm.product_qty,0))
                        from 
                            purchase_order_line pol
                        left join
                            stock_move sm on pol.id=purchase_line_id
                        left join
                            stock_picking sp on sm.picking_id=sp.id
                        where
                            sm.state='done' and pol.id in (%s) and sp.state not in ('draft','cancel')
                        Group by pol.id""" % (pol_ids))
            for id,qty in cr.fetchall():
                res[id]=qty
        return res
    
    _columns = {                
                'location_id':fields.many2one('stock.location', 'From Stock'),
                'location_dest_id':fields.many2one('stock.location', 'To Stock'),
                'received_qty': fields.function(_get_product_received_qty,type='float',string='Qty.',method=True),
                }

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            full_name = (record.product_id.default_code + " - " + record.name) if context.get('show_productCode', False) else record.name
            res.append((record.id, full_name))
        return res