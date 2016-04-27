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
from openerp.tools.translate import _

class StockMove(osv.osv):
    _inherit = 'stock.move'
    _name="stock.move"

    def _get_qty_inout(self, cr, uid, ids, name, args, context):
        if not context:
            context = {}
        res = {}
        location_ids = context.get('location_ids', False)
        if type(location_ids) == type(1):
            location_ids = [location_ids]
        elif type(location_ids) != type([]):
            location_ids = []
        if not location_ids:
            location_obj = self.pool.get('stock.location')
            location_ids = location_obj.search(cr, uid, [('general_stock','=',True)])
        for sm in self.browse(cr, uid, ids, context):
            #If stock source -> Negative number (In case move negative pls consider later)
            if sm.location_id.id in location_ids:
                res[sm.id] = - sm.product_qty
            else:
                res[sm.id] = sm.product_qty
        return res

    def _check_warehouse_product_available(self, cr, uid, ids, context = {}):
        #Fixme: Later If using convert Product Qty and Uom
        #Check enough Qty from Source Warehouse before move (Only internal)
        context = context or {}
        ctx = context.copy()
        ctx['except_move_ids'] =  ids or [0] #Not calculation quantity for check move

        pp_obj = self.pool.get('product.product')
        location_list = {}

        #Get product and Qty list
        for sm in self.browse(cr, uid, ids):
            if sm.state not in ('draft','cancel') and sm.location_id.usage=='internal':
                pp_lists = location_list.get(sm.location_id.id, {})
                pp_id = sm.product_id.id
                pp_lists[pp_id] = sm.product_qty + pp_lists.get(pp_id, 0)
                location_list[sm.location_id.id] = pp_lists
        #Check available List Product
        errorList = []
        for loc_id in location_list:
            pp_lists = location_list[loc_id]
            search_product = [('id','in', pp_lists.keys())]
            ctx['filter_by_location_id'] = loc_id
            ctx['location_ids'] = [loc_id]
            products_available_ids = pp_obj.search(cr, uid, search_product, context=ctx)
            pp_list_res = pp_obj.read(cr, uid, products_available_ids, ['qty_available'], context = ctx)
            pp_dict_res = {x['id']:x['qty_available'] for x in pp_list_res}
            for ppID in pp_lists:
                if ppID not in pp_dict_res or pp_dict_res[ppID] < pp_lists[ppID]:
                    pCode = pp_obj.read(cr, uid, ppID, ['default_code'])['default_code']
                    warehouse = self.pool.get('stock.location').read(cr, uid, loc_id, ['name'])['name']
                    errorList.append("%s @ %s: %s(Available) - %s (Request)" % (pCode, warehouse, pp_dict_res.get(ppID,0), pp_lists.get(ppID,0)))
        if errorList:
            raise osv.except_osv(_("KDERP Warning"),_("Please check product(s) below, not enough quantity in stock\n %s" % "\n".join(errorList)))
            return False
        return True

    # def _check_picking_type(self, cr, uid, ids):
    #     picking_dict = {'customer-internal':'in',
    #                     'supplier-internal':'in',
    #                     'internal-internal':'internal',
    #                     'internal-supplier':'out',
    #                     'internal-customer':'out'}
    #     for sm in self.browse(cr, uid, ids):
    #         if sm.picking_id and sm.picking_id.type != picking_dict[sm.location_id.usage + "-" + sm.location_dest_id.usage]:
    #             move_type = picking_dict[sm.location_id.usage + "-" + sm.location_dest_id.usage]
    #             picking_type = sm.picking_id.type
    #             raise osv.except_osv(_("KDERP Warning"),_("Please check Picking type (%s) and Detail picking(%s)" % (picking_type.upper(), move_type.upper())))
    #     return True

    _columns ={
        'qty_inout':fields.function(_get_qty_inout,type='float',string='Qty. In/Out'),
        'purchase_id':fields.related('purchase_line_id','order_id',type='many2one',string='PO. No.',relation='purchase.order'),
        'remarks':fields.char("Remarks", size=128, states={'done': [('readonly', True)]})
    }
    _constraints = [(_check_warehouse_product_available, "KDERP Warning, Please Quantity available in Warehoues", ['product_id','product_qty','location_id'])]
    #(_check_picking_type, "KDERP Warning, Check Picking type",['location_id','location_dest_id','picking_id'])
    # _defaults = {
    #    'location_id':lambda self, cr, uid, context = {}: context.get('location_id',False) if context else False,
    #    'location_dest_id':lambda self, cr, uid, context = {}: context.get('location_dest_id',False) if context else False
    #     }

    #TODO
    # #Kiem tra lai Product Qty con so luong hay khong khi submit
        # search_product = [('id','in', pp_ids)]
        # pp_obj = self.pool.get('product.product')
        # products_available_ids = pp_obj.search(cr, uid, search_product, context=context)
        # pp_list = pp_obj.read(cr, uid, products_available_ids, ['qty_available'], context = context)
        # pp_dict = {pp['id']: pp['qty_available'] for pp in pp_list if pp['qty_available']>0}
    # Kiem tra O trong 01 Stock Picking co cung chieu in, out hay internal khong