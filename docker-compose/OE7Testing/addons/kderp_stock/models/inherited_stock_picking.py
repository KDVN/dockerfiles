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
from openerp import netsvc

from tools.translate import _

EXPLAIN_PACKING_NO = _("""Packing Number:
                            P(L)(IN)YY-XXXXX,
                            P: Packing,
                            (L) Location H: Hanoi, P: Hai Phong, S: Ho Chi Minh,
                            (IN) Packing in, OUT Packing Out, (M) Stock Move (Internal),
                            YY Year,
                            XXXXX is increase number with 5 number """)

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _name = 'stock.picking'

    def get_newcode(self, cr, uid, type = 'internal', context = {} ):
        if not context:
            context = {}
        if not type:
            type = context.get('picking_type', 'internal')

        type = 'int' if type == 'internal' else type
        # Please consider later when location user global (location code)
        cr.execute("""SELECT
                        replace(prefix,'$',location_code) || to_char(current_date,replace(suffix,'I','"I"')) ||lpad((max(substring(coalesce(sp.name, replace(prefix,'$',location_code) || to_char(current_date,replace(suffix,'I','"I"')) || lpad('0',padding,'0')) from length(replace(prefix,'$',location_code) || to_char(current_date,replace(suffix,'I','"I"')))+1 for padding)::integer) + 1)::text, padding, '0')
                    FROM
                        (select
                                case when location_user = 'hcm' then 'S' else
                                    case when location_user = 'haiphong' then 'P' else 'H' end end as location_code from res_users ru where ru.id = %d ) vwcompany
                    left join
                        ir_sequence isq on 1=1
                    left join
                         stock_picking sp on sp.name ilike replace(isq.prefix,'$',location_code) || to_char(current_date,replace(suffix,'I','"I"')) || lpad('_',padding,'_')
                    WHERE
                        isq.code ilike 'kderp_stock_picking_code_%%%s'
                    group by
                        isq.id,
                        location_code""" % (uid,type))
        new_code = cr.fetchone()
        return new_code[0] if new_code else False

    # Fuction
    # Change state selection
    # Get id of view when open Picking In, Out, or Move (internal)
    def fields_get(self, cr, uid, fields=None, context=None):
        res = super(stock_picking, self).fields_get(cr, uid, fields, context)
        picking_id = context.get('picking_id',False)
        picking_type = context.get('picking_type','in')
        if picking_id:
            picking_type = self.read(cr, uid, picking_id, ['type'])['type']
        selection = picking_type!='in' and res.get('state')
        if selection:
            newStates = [('draft','Creating'),('assigned', 'Waiting for Delivery'),('done', 'Received'),('cancel', 'Cancelled')] if picking_type=='out' else \
                        [('draft','Creating'),('assigned', 'Waiting for Receive'),('done', 'Received'),('cancel', 'Cancelled')]
            selection['selection'] = newStates
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if not context:
            context = {}
        picking_id = context.get('picking_id',False)
        if picking_id:
            picking_type = self.read(cr, uid, picking_id, ['type'])['type']
            if picking_type and not view_id:
                views_ids = self.pool.get('ir.ui.view').search(cr, uid, [('name','=','kderp.stock.picking.%s.%s' % (picking_type,view_type))])
                if views_ids:
                    view_id = views_ids[0]
        elif context.get('picking_type', False) and not view_id:
                picking_type = context.get('picking_type', False)
                views_ids = self.pool.get('ir.ui.view').search(cr, uid, [('name','=','kderp.stock.picking.%s.%s' % (picking_type,view_type))])
                if views_ids:
                    view_id = views_ids[0]
        res = super(stock_picking, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        # selection = picking_type!='in' and res.get('fields',{}) and res.get('fields',{}).get('state')
        # if selection:
        #     newStates = [('draft','Creating'),('assigned', 'Waiting for Delivery'),('done', 'Received'),('cancel', 'Cancelled')] if picking_type=='out' else [()]
        #     selection['selection'] = newStates
        return res

    def create(self, cr, user, vals, context=None):
        if not context:
            context = {}
        if ('name' not in vals) or (vals.get('name')=='/'):
            vals['name'] = self.pool.get('stock.picking').get_newcode(cr, user, context.get('picking_type','internal'), context)
        new_id = super(stock_picking, self).create(cr, user, vals, context)
        return new_id

    def action_cancel(self, cr, uid, ids, context=None):
        """ Changes picking state to cancel.
        @return: True
        """
        if not len(ids):
            return False
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            wf_service.trg_delete(uid, 'stock.picking', pick.id, cr)
            ids2 = [move.id for move in pick.move_lines]
            self.pool.get('stock.move').action_cancel(cr, uid, ids2, context)
        self.write(cr, uid, ids, {'state': 'cancel', 'invoice_state': 'none'})
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        """ Revise picking status.
        @return: True
        """
        if not len(ids):
            return False
        wf_service = netsvc.LocalService("workflow")

        for pick in self.browse(cr, uid, ids, context=context):
            ids2 = [move.id for move in pick.move_lines]
            self.pool.get('stock.move').action_cancel_draft(cr, uid, ids2, context)
            wf_service.trg_delete(uid, 'stock.picking', pick.id, cr)
            self.write(cr, uid, [pick.id], {'state': 'draft'})
            wf_service.trg_create(uid, 'stock.picking', pick.id, cr)
        return True

    def _get_received_by_id(self, cr, uid, context={}):
        res_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid),('department_id','=','S1420')])
        return res_ids[0] if res_ids else False

    #Copy from Original
    def _set_maximum_date(self, cr, uid, ids, name, value, arg, context=None):
        """ Calculates planned date if it is greater than 'value'.
        @param name: Name of field
        @param value: Value of field
        @param arg: User defined argument
        @return: True or False
        """
        if not value:
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        for pick in self.browse(cr, uid, ids, context=context):
            sql_str = """update stock_move set
                    date_expected='%s'
                where
                    picking_id=%d """ % (value, pick.id)
            if pick.max_date:
                sql_str += " and (date_expected='" + pick.max_date + "')"
            cr.execute(sql_str)
        return True

    def _set_minimum_date(self, cr, uid, ids, name, value, arg, context=None):
        """ Calculates planned date if it is less than 'value'.
        @param name: Name of field
        @param value: Value of field
        @param arg: User defined argument
        @return: True or False
        """
        if not value:
            return False
        if isinstance(ids, (int, long)):
            ids = [ids]
        for pick in self.browse(cr, uid, ids, context=context):
            sql_str = """update stock_move set
                    date_expected='%s'
                where
                    picking_id=%s """ % (value, pick.id)
            if pick.min_date:
                sql_str += " and (date_expected='" + pick.min_date + "')"
            cr.execute(sql_str)
        return True

    def get_min_max_date(self, cr, uid, ids, field_name, arg, context=None):
        """ Finds minimum and maximum dates for picking.
        @return: Dictionary of values
        """
        res = {}
        for id in ids:
            res[id] = {'min_date': False, 'max_date': False}
        if not ids:
            return res
        cr.execute("""select
                picking_id,
                min(date_expected),
                max(date_expected)
            from
                stock_move
            where
                picking_id IN %s
            group by
                picking_id""",(tuple(ids),))
        for pick, dt1, dt2 in cr.fetchall():
            res[pick]['min_date'] = dt1
            res[pick]['max_date'] = dt2
        return res

    def _get_pickings(self, cr, uid, ids, context=None):
        res = set()
        for move in self.browse(cr, uid, ids, context=context):
            if move.picking_id and not move.picking_id.min_date < move.date_expected < move.picking_id.max_date:
                res.add(move.picking_id.id)
        return list(res)

    def _check_picking_type_and_location(self, cr, uid, ids, context):
        context = {} and context
        picking_dict = {'customer-internal':'in',
                        'supplier-internal':'in',
                        'internal-internal':'internal',
                        'internal-supplier':'out',
                        'internal-customer':'out'}
        for sp in self.browse(cr, uid, ids):
            if picking_dict[sp.location_id.usage + "-" + sp.location_dest_id.usage] != sp.type or sp.location_id.usage=='view' or sp.location_dest_id.usage=='view':
                return False
            for sm in sp.move_lines:
                if sp.type != picking_dict[sm.location_id.usage + "-" + sm.location_dest_id.usage]:
                    move_type = picking_dict[sm.location_id.usage + "-" + sm.location_dest_id.usage]
                    picking_type = sm.picking_id.type
                    raise osv.except_osv(_("KDERP Warning"),_("Please check Picking type: %s and Detail of Picking: %s" % (picking_type.upper(), move_type.upper())))
        return True

        return True

    STOCK_PICKING_IN_STATE = [('draft', 'Waiting for Confirmation'),
            # ('auto', 'Waiting Another Operation'),
            ('confirmed', 'Confirmed'),
            ('assigned', 'Waiting for Delivery'),
            ('done', 'Received'),
            ('cancel', 'Cancelled'),]
    DOMAIN_LOCATION = [('usage','in',('supplier','internal','customer'))]
    _columns = {
                'name': fields.char('Packing No.', size=16, select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]},required=True, help=EXPLAIN_PACKING_NO),
                'origin':fields.char('Ref. No.', size=32),

                'check_payment':fields.many2one('kderp.supplier.payment', 'Supplier Payment'),
                'received_date':fields.date('Received Date'),

                'state':fields.selection(STOCK_PICKING_IN_STATE,'State', readonly=1),

                'move_lines': fields.one2many('stock.move', 'picking_id', 'Detail Moves', states={'cancel': [('readonly', True)]}, copy=True),

                #Set location required
                'location_id': fields.many2one('stock.location', 'Source Warehouse', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}, domain = DOMAIN_LOCATION,
                                                    help="Select a source warehouse", select=True, required=True),
                'location_dest_id': fields.many2one('stock.location', 'Dest. Warehouse', states={'done':[('readonly', True)], 'cancel':[('readonly',True)]},domain = DOMAIN_LOCATION,
                                                    help="Select a destination warehouse", select=True, required=True),


                'storekeeper_incharge_id':fields.many2one('hr.employee','Storekeeper', required=True, states={'done':[('readonly', True)]}),

                'min_date': fields.function(get_min_max_date, fnct_inv=_set_minimum_date, multi="min_max_date",
                            store={'stock.move': (_get_pickings, ['date_expected', 'picking_id'], 20)}, type='date', string='Scheduled', select=1, help="Scheduled date for the shipment to be processed"),
                'date': fields.date('Creation Date', help="Creation date, usually the time of the order.", select=True, states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
                'date_done': fields.date('Date of Transfer', help="Date of Completion", states={'done':[('readonly', True)], 'cancel':[('readonly',True)]}),
                'max_date': fields.function(get_min_max_date, fnct_inv=_set_maximum_date, multi="min_max_date",
                         store={'stock.move': (_get_pickings, ['date_expected', 'picking_id'], 20)}, type='date', string='Max. Expected Date', select=2),
                }

    _defaults = {
                'storekeeper_incharge_id': _get_received_by_id,
                'name': lambda self, cr, uid, context ={}: self.pool.get('stock.picking').get_newcode(cr, uid, False, context),
                'type': lambda self, cr, uid, context ={}: 'internal' if not context else context.get('picking_type','internal')
                }
    _constraint = [(_check_picking_type_and_location,'Please check picking type and Source Warehouse and Destination Warehouse',['type','location_id','location_dest_id'])]

    def update_stock_received(self,cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state':'done'})
        return True

    def update_stock_draft(self,cr, uid, ids, *args):
        self.write(cr,uid,ids,{'state':'draft'})
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms picking.
        @return: True
        """
        pickings = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        todo = []
        for picking in pickings:
            if picking.purchase_id:
                if not picking.purchase_id.state in ('waiting_for_delivery','waiting_for_payment','done','revising'):
                    raise osv.except_osv("KDERP Warning", """Can't receive this picking because purchase belong not yet approved""")
            for r in picking.move_lines:
                if r.state == 'draft':
                    todo.append(r.id)
        todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)
            self.pool.get('stock.move').force_assign(cr, uid, todo, context=context)
        return True