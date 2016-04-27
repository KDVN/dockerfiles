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
import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv, orm
from kderp_base import kderp_base
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

from openerp import netsvc, SUPERUSER_ID
from encodings.punycode import digits

class kderp_prepaid_purchase_order(osv.osv):
    _name = 'kderp.prepaid.purchase.order'
    _description = 'KDERP Prepaid Purchase Order'
    
    def unlink(self, cr, uid, ids, context=None):
        for ppo in self.browse(cr, uid, ids):
            if ppo.state<>'draft':
                raise osv.except_osv(_('Error!'), _('You can remove a Prepaid Purchase with state is Draft only'))
        return super(kderp_prepaid_purchase_order, self).unlink(cr, uid, ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        res=[]
        for record in self.browse(cr, uid, ids):
            name = "%s - %s" % (record.name, record.description)  
            res.append((record['id'], name))
        return res
    
    def action_draft_to_approved(self, cr, uid, ids, context = {}):
        val = {'state':'approved'}
        self.write(cr, uid, ids, val, context)   
        picking_ids = []
        for order in self.browse(cr, uid, ids):
            picking_ids.extend(self._create_pickings(cr, uid, order, order.prepaid_order_line, None, context=context))

        # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
        # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
        # one that should trigger the advancement of the purchase workflow.
        # By default we will consider the first one as most important, but this behavior can be overridden.
        return picking_ids[0] if picking_ids else False
    
    def action_reject(self, cr, uid, ids, context = {}):
        if not context:
            context = {}
        for ppo in self.browse(cr, uid, ids, context):
            for pk in ppo.packing_ids:
                if pk not in ('draft','cancel'):
                    raise osv.except_osv("KDERP Warning", "State in packing related not in draft")
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    SELECTION_STATE = [('draft','Draft'),
                       ('approved','Approved'),
                       ('done','Done'),
                       ('cancel','Rejected')]
    
    def onchange_date(self, cr, uid, ids, oldno, date):
        val = {}
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
                                    kderp_prepaid_purchase_order.name as code
                                FROM 
                                    kderp_prepaid_purchase_order
                                WHERE
                                    length(kderp_prepaid_purchase_order.name::text)=
                                    ((SELECT 
                                    length(prefix || suffix) + padding AS length
                                    FROM 
                                    ir_sequence
                                    WHERE 
                                    ir_sequence.code::text = 'kderp_prepaid_order_code'::text LIMIT 1))
                                ) cnewcode ON cnewcode.code::text ~~ (isq.prefix || to_char(DATE '%s',  suffix || lpad('_',padding,'_'))) and isq.code::text = 'kderp_prepaid_order_code'::text  
                            WHERE isq.active and isq.code::text = 'kderp_prepaid_order_code') wnewcode
                        GROUP BY 
                            pattern, 
                            name,
                            seq_code,
                            prefix,
                            padding""" %(date,date,date,date))
            res = cr.fetchone()
            if res:
                val={'name':res[0]}
        
        return {'value':val}
    
    #Field Funtion Area
    def _get_tax_default(self,cr,uid,context):
        tax_ids = self.pool.get('account.tax').search(cr, uid,[('type_tax_use','=','purchase'),('active','=',True),('default_tax','=',True)])
        return tax_ids
    
    def _get_prepaid_from_detail(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('kderp.prepaid.purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.prepaid_order_id.id] = True
        return result.keys()
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for ppo in self.browse(cr, uid, ids, context=context):
            res[ppo.id] = {
                'amount_untaxed': 0.0,
                'amount_total': 0.0,
                'amount_tax':0.0
                }
            val = 0.0
            val1=0.0
            
            for line in ppo.prepaid_order_line:
                val += line.subtotal
            
            for c in self.pool.get('account.tax').compute_all(cr, uid, ppo.taxes_id, val, 1, False, False)['taxes']:
                val1 += c.get('amount', 0.0)
            
            res[ppo.id]['amount_untaxed'] = val
            res[ppo.id]['amount_tax'] = val1            
            res[ppo.id]['amount_total'] = val1 + val
            
        return res
    _order="date desc, name desc"
    _columns={
                'name':fields.char('Code', required = True, size=16, select=1, readonly = True, states={'draft':[('readonly', False)]}),
                'description':fields.char('Description', required = True, size=256, readonly = True, states={'draft':[('readonly', False)]}),
                'date':fields.date('Order Date', select = 1, required = True, readonly = True, states={'draft':[('readonly', False)]}),
                
                'partner_id':fields.many2one('res.partner', 'Supplier', ondelete='restrict', required=True, readonly = True, states={'draft':[('readonly', False)]} , change_default=True),
                'address_id':fields.many2one('res.partner', 'Address', ondelete='restrict', required=True, readonly = True, states={'draft':[('readonly', False)]}),
                'currency_id':fields.many2one('res.currency','Curr', required=True, readonly = True, states={'draft':[('readonly', False)]}),
                
                'packing_ids':fields.one2many('stock.picking','prepaid_purchase_order_id','Packing List', readonly = True),
                
                'prepaid_order_line':fields.one2many('kderp.prepaid.purchase.order.line', 'prepaid_order_id', readonly = True, states={'draft':[('readonly', False)]}),
                
                'state':fields.selection(SELECTION_STATE, 'State', readonly = True),
                
                'taxes_id': fields.many2many('account.tax', 'prepaid_purchase_vat_tax', 'prepaid_purchase_vat_id', 'tax_id', 'VAT (%)', states={'draft':[('readonly', False)]}, readonly = True),
                            
                'amount_untaxed':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'),string='Amount',type='float', method=True, multi="kderp_expense_total",
                                                  store={
                                                          'kderp.prepaid.purchase.order.line': (_get_prepaid_from_detail, ['price_unit', 'product_qty'], 20),
                                                          'kderp.prepaid.purchase.order':(lambda self, cr, uid, ids, context = {}: ids, ['taxed_ids'], 20)
                                                         }),
                'amount_tax':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'),string='VAT',type='float', method=True, multi="kderp_expense_total",
                                                  store={
                                                         'kderp.prepaid.purchase.order.line': (_get_prepaid_from_detail, ['price_unit', 'product_qty'], 20),
                                                         'kderp.prepaid.purchase.order':(lambda self, cr, uid, ids, context = {}: ids, ['taxed_ids'], 20)
                                                         }),
                'amount_total':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'), string='Total',type='float', method=True, multi="kderp_expense_total",
                                                store={
                                                        'kderp.prepaid.purchase.order.line': (_get_prepaid_from_detail, ['price_unit', 'product_qty'], 20),
                                                        'kderp.prepaid.purchase.order':(lambda self, cr, uid, ids, context = {}: ids, ['taxed_ids'], 20)
                                                       }),
              }
    
    _defaults = {
                 'date': lambda *a: time.strftime('%Y-%m-%d'),
                 'state': lambda *x: 'draft',
                 'partner_id':lambda self, cr, uid, context={}: context.get('partner_id',False),
                 'currency_id':lambda self, cr, uid, context={}:self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id,
                 'taxes_id':_get_tax_default
                 }
    
    _sql_constraints=[('kderp_prepaid_purchase_code_unique','unique(name)','Prepaid Purchase Code must be unique !')]
    
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
                }}
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
        supplier = partner.browse(cr, uid, partner_id)
        return {'value': {'address_id': supplier.id or False }}
    
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
    
    def _prepare_order_picking(self, cr, uid, order, context=None):
        return {
            #'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in'),
            'name': self.pool.get('stock.picking').get_newcode(cr, uid, 'in', context),
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date, context),
            'partner_id': order.partner_id.id,
            'invoice_state': 'none', 
            'type': 'in',
            'prepaid_purchase_order_id': order.id,
            #'company_id': order.company_id.id,
            'move_lines' : [],
        }
    
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        price_unit = order_line.price_unit
#        if order.currency_id.id != order.company_id.currency_id.id:
            #we don't round the price_unit, as we may want to store the standard price with more digits than allowed by the currency
#            price_unit = self.pool.get('res.currency').compute(cr, uid, order.currency_id.id, order.company_id.currency_id.id, price_unit, round=False, context=context)
        return {
            'name': order_line.name or '',
            'product_id': order_line.product_id.id,
            'product_qty': order_line.product_qty,
            'product_uos_qty': order_line.product_qty,
            'product_uom': order_line.product_uom.id,
            'product_uos': order_line.product_uom.id,
            'date': self.date_to_datetime(cr, uid, order.date, context),
            #'date_expected': self.date_to_datetime(cr, uid, order_line.date_planned, context),
            'location_id': order.partner_id.property_stock_supplier.id,
            'location_dest_id': order_line.location_id.id,
            'picking_id': picking_id,
            'partner_id': order.partner_id.id,
            #'move_dest_id': order_line.move_dest_id.id,
            'state': 'draft',
            'type':'in',
            'prepaid_purchase_line_id': order_line.id,
            #'company_id': order.company_id.id,
            'price_unit': price_unit
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
        if not picking_id:
            picking_id = self.pool.get('stock.picking').create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
            
        todo_moves = []
        stock_move = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        for order_line in order_lines:
            if not order_line.product_id:
                continue
            if order_line.product_id.type in ('product', 'consu'):
                move = stock_move.create(cr, uid, self._prepare_order_line_move(cr, uid, order, order_line, picking_id, context=context))
                #if order_line.move_dest_id and order_line.move_dest_id.state != 'done':
                #    order_line.move_dest_id.write({'location_id': order.location_id.id})
                todo_moves.append(move)
        stock_move.action_confirm(cr, uid, todo_moves)
        stock_move.force_assign(cr, uid, todo_moves)
        stock_move.action_done(cr, uid, todo_moves)
        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return [picking_id]

    def action_picking_create(self, cr, uid, ids, context=None):
        picking_ids = []
        for order in self.browse(cr, uid, ids):
            picking_ids.extend(self._create_pickings(cr, uid, order, order.prepaid_order_line, None, context=context))

        # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
        # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
        # one that should trigger the advancement of the purchase workflow.
        # By default we will consider the first one as most important, but this behavior can be overridden.
        return picking_ids[0] if picking_ids else False
    
kderp_prepaid_purchase_order()

class kderp_prepaid_purchase_order_line(osv.osv):
    _name = 'kderp.prepaid.purchase.order.line'
    _description = 'kderp.prepaid.purchase.order.line'
    
    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        res=[]
        if context.get('group_by') == 'prepaid_order_line_id':
            for record in self.browse(cr, uid, ids):
                name = "%s - %s" % (record.name, ("Total Qty. : "+"{:,.2f}".format(record.product_qty)))  
                res.append((record['id'], name))
        else:
            for record in self.browse(cr, uid, ids):
                res.append((record['id'], record.name))
        return res
    
    def onchange_product_id(self, cr, uid, ids, product_id, name, qty, uom_id, price_unit, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
  
        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            res = {'value': {'price_unit': 0.0, 'name': '', 'product_uom' : False}}
            return res
  
        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        
        product = product_product.browse(cr, uid, product_id, context)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name:
            dummy, name = product_product.name_get(cr, uid, product_id, context,from_obj='pol')[0]
            if product.description_purchase:
                name = product.description_purchase
        res['value'].update({'name': name})
  
        # - set a domain on product_uom
#        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}
  
        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id
  
        res['value'].update({'product_uom': uom_id})
  
        # - determine product_qty and date_planned based on seller info 
        qty = qty or 1.0
        
        if qty:
            res['value'].update({'product_qty': qty})
  
        return res
    
    def _get_subtotal(self, cr, uid, ids, name, args, context={}):
        if not context:
            context = {}
        res = {}
        for ppol in self.browse(cr, uid, ids, context):
            res[ppol.id] = ppol.product_qty * ppol.price_unit
        return res
    
    def _get_new_seq(self, cr, uid, context={}):
        from kderp_base import kderp_base
        if not context:
            context={}
        new_val = kderp_base.get_new_from_tree(cr, uid, context.get('id',False), self,context.get('lines',[]),'sequence', 1, 1, context)
        return new_val
    
    SELECTION_STATE = [('doing','Doing'),                       
                       ('done','Done')]
    _columns={
              'sequence':fields.integer("Seq."),
              'product_id':fields.many2one('product.product','Product', required = True),
              'product_uom':fields.many2one('product.uom', 'Unit', required = True, digits=(16,2)),
              'product_qty':fields.float("Quantity", required = True),
              'price_unit':fields.float('Price Unit', required = True, digits_compute=dp.get_precision('Amount')),
              'name':fields.char('Description', required = True, size = 128),
              'location_id':fields.many2one('stock.location', 'Destination', required = True, domain = [('usage','=','internal')]),
              'prepaid_order_id':fields.many2one('kderp.prepaid.purchase.order','Prepaid Order'),
              'state':fields.selection(SELECTION_STATE, 'State', readonly = True),
              
              'subtotal':fields.function(_get_subtotal, type='float', digits=(16,2), method= True, string='Sub-Total',
                                         store={
                                                'kderp.prepaid.purchase.order.line': (lambda self, cr, uid, ids, context = {}: ids, ['product_qty', 'price_unit','prepaid_order_id'], 15) 
                                                })
              }
    _defaults = {
                 'product_id': lambda self, cr, uid, context = {}: kderp_base.get_new_value_from_tree(cr, uid, context.get('id',False), self, context.get('prepaid_order_line',[]), 'product_id', context),
                 'product_uom': lambda self, cr, uid, context = {}: kderp_base.get_new_value_from_tree(cr, uid, context.get('id',False), self, context.get('prepaid_order_line',[]), 'product_uom', context),
                 'location_id': lambda self, cr, uid, context = {}: kderp_base.get_new_value_from_tree(cr, uid, context.get('id',False), self, context.get('prepaid_order_line',[]), 'location_id', context),
                 'price_unit': lambda *x: 0.0,
                 'sequence':_get_new_seq
                 }
    
    def action_open_line_detail(self, cr, uid, ids, context):
        if not context:
            context = {}
        context['search_default_group_order_line'] = True
        res_action = {
                    'type': 'ir.actions.act_window',
                    'domain': [('prepaid_order_line_id','in', ids)],
                    'res_model':'kderp.prepaid.purchase.order.line.detail',
                    'name': _('Allocated Detail'),
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'context': context
                    }
        return res_action