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
from openerp import tools
from bsddb.dbtables import _columns

class stock_location(osv.osv):
    _inherit = 'stock.location'
    _name = 'stock.location'
    _columns = {
                'global_stock':fields.boolean("Global?",help= "Using for HANOI and Ho Chi Minh"),
                'stock_code':fields.char("Stock Code", size=32, help='This code is very important for Global Stock, this code is using for matching stock between two server'),
                'default_project_stock':fields.boolean("Default Project Stock"),
                
                'product_details':fields.one2many('stock.location.product.detail','location_id','Details', readonly = 1)
                }
        
class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    
    _columns = {
        'prepaid_purchase_order_id': fields.many2one('kderp.prepaid.purchase.order', 'Purchase Order',
            ondelete='restrict', select=True),
    }

    _defaults = {
        'prepaid_purchase_order_id': False,
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = super(stock_picking, self).write(cr, uid, ids, vals, context=context)
        from openerp import netsvc
        wf_service = netsvc.LocalService("workflow")
        if vals.get('state') in ['done']:
            for sp in self.browse(cr, uid, ids, context=context):
                    if sp.purchase_id.state == 'waiting_for_delivery':
                        wf_service.trg_validate(uid, 'purchase.order', sp.purchase_id.id, 'btn_roa_completed_delivered', cr)
        return res
    
class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    SELECTION_STATE = [('doing','Doing'),                       
                       ('done','Done')]
    
    
    def _get_move_from_company(self, cr, uid, ids, context=None):
        res=[]
        cr.execute('select id from stock_move where prepaid_purchase_line_id is not null and company_id is not null')
        for id in cr.fetchall():
            res.append(id[0])
        return res
    
    def _get_movecode(self, cr, uid, ids, name, args, context):
        res = {}
        for sm in self.browse(cr, uid, ids):
            if sm.prepaid_purchase_line_id:
                res[sm.id] = int(sm.company_id.location_code + str(sm.id))
            else:
                res[sm.id] = False
        return res
    
    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms stock move.
        @return: List of ids.
        """        
        check_error = self.pool.get('stock.location.product.detail').check_prepaid_product_availability(cr, uid, ids)
        res = super(stock_move, self).action_confirm(cr, uid, ids, context)
        return res
    
    def force_assign(self, cr, uid, ids, context=None):
        check_error = self.pool.get('stock.location.product.detail').check_prepaid_product_availability(cr, uid, ids)
        res = super(stock_move, self).force_assign(cr, uid, ids, context)
        return res
    
    _columns = {
        'prepaid_purchase_line_id': fields.many2one('kderp.prepaid.purchase.order.line',
                                                    'Prepaid Purchase Order Line', ondelete='restrict', select=True),
        'global_state':fields.selection(SELECTION_STATE, 'Global State', readonly = True, help='Using for Global Stock only', select = 1),
        'source_move_code':fields.integer('Source Move Code', select = 1),
        'move_code':fields.function(_get_movecode, type='integer',  method = True,select = 1,
                                                store={
                                                     'stock.move':(lambda self, cr, uid, ids, c={}: ids, ['id','prepaid_purchase_line_id'],50),
                                                     'res.company':(_get_move_from_company,['location_code'],50)
                                                      }),
    }
    
    _defaults ={
                'global_state':'doing'
                }
    
    def _check_product_id(self, cr, uid, ids, context=None):
        """
            Kiem tra product id and purchase_line_id
        """
        if not context:
            context={}
        for sm in self.browse(cr, uid, ids, context=context):
            res = True
            if sm.product_id:
                if sm.purchase_line_id and sm.prepaid_purchase_line_id:
                    res = False
                elif sm.purchase_line_id:            
                    if sm.purchase_line_id.product_id.id !=  sm.product_id.id:
                        res = False
                elif sm.prepaid_purchase_line_id:
                    if sm.prepaid_purchase_line_id.product_id.id !=  sm.product_id.id:
                        res = False
        return res
    
    _constraints = [(_check_product_id, 'KDERP Warning, Please Product and Purchase Line', ['purchase_line_id','product_id'])]
    

stock_move()

class stock_location_product_detail(osv.osv):
    _auto = False
    _name = 'stock.location.product.detail'
    _description = 'List of product Available in Stock'
    
    def check_access_rights(self, cr, uid, operation, raise_exception=True): # no context on purpose.
        self.pool.get('kderp.link.server').check_server_connection(cr, uid, [], {})                
        return super(stock_location_product_detail, self).check_access_rights(cr, uid, operation, raise_exception)
    
    def check_prepaid_product_availability(self, cr, uid, move_codes_ids, context = {}):
        """
            Check product availability in stock or not
            ({}) -> False is everything thing is ok 
        """
        tmp_move_code = []
        check_move_codes = {}
        stm_obj = self.pool.get('stock.move')
        for move in stm_obj.browse(cr, uid, move_codes_ids, context=context):
            source_move_code = move.source_move_code             
            if move.source_move_code:                
                if move.source_move_code in check_move_codes:
                    check_move_codes[source_move_code] += move.product_qty
                else:
                    check_move_codes[source_move_code] = move.product_qty
                tmp_move_code.append(source_move_code)
                    
        slpd_ids = self.search(cr, uid, [('move_code', 'in', tmp_move_code)])
        list_errors = []
        for pd in self.browse(cr, uid, slpd_ids):
            if check_move_codes[pd.move_code] > pd.available_qty:
                error = '%s: only available %s (%s) to allocate (Your Request: %s)' % (pd.product_id.code, pd.available_qty, pd.product_uom.name, check_move_codes[pd.move_code])
                list_errors.append(error)
        if list_errors:
            raise osv.except_osv("KDERP Warning",'\n'.join(map(str, list_errors)))
        return True
    
    _columns  = {
                 'location_id':fields.many2one('stock.location', 'Stock'),
                 'product_id':fields.many2one('product.product','Product'),
                 'product_uom':fields.many2one('product.uom', 'Uom'),
                 'price_unit':fields.float('Price Unit',digits=(16,2)),
                 'prepaid_amount':fields.float('Prepaid Amt.',digits=(16,2)),
                 'allocated_amount':fields.float('All. Amt.',digits=(16,2)),
                 'remaining_amount':fields.float('Remaing Amt.',digits=(16,2)),
                 'quantity':fields.float('Qty.', digits=(16,2)),
                 'allocated_qty':fields.float('Allocated Qty.', digits=(16,2)),
                 'available_qty':fields.float('Available Qty.', digits=(16,2)),
                 'requesting_qty':fields.float('Requesting Qty.', digits=(16,2)),
                 'move_code':fields.integer('Move Code'),
                 'origin':fields.char('Origin', size=32),                 
                 'product_description':fields.char('Desc', size=256),
                 }
    
    def init(self, cr):
        #Create user connect
        new_role = 'stock_remote'
        cr.execute("""SELECT * FROM pg_catalog.pg_user WHERE usename = '%s'""" % new_role)
        if not cr.rowcount:
            #Create User
            cr.execute("""CREATE ROLE stock_remote LOGIN PASSWORD '290797!sr' NOSUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION;""")
            #Grant Permission
            cr.execute("""                        
                        GRANT SELECT ON
                                        product_product, 
                                        product_uom, 
                                        stock_location, 
                                        purchase_order_line, 
                                        account_analytic_account 
                        TO %s ;
                        GRANT ALL ON stock_move TO %s ;""" % (new_role, new_role))        
        
        vwName = 'stock_location_product_detail'
        checkView1 = 'vwstock_move_remote'
        cr.execute("""SELECT 1  FROM  information_schema.views where table_name = '%s'""" % checkView1)
        if cr.rowcount:            
            tools.drop_view_if_exists(cr, vwName)
            cr.execute("""
                        Create or replace view %s as 
                            ---***********STOCK IN ***************************
                            Select
                                        row_number() over (order by vwin.location_id, vwin.move_code) as id,
                                        vwin.location_id,
                                        vwin.product_uom,
                                        vwin.move_code,
                                        vwin.source_move_code,
                                        vwin.origin,
                                        vwin.product_description,
                                        vwin.quantity,
                                        vwin.product_id,
                                        vwin.price_unit,
                                        vwin.price_unit*vwin.quantity as prepaid_amount, 
                                        sum(case when vwout.state='confirmed' then 0 else coalesce(vwout.quantity,0) end ) as allocated_qty,
                                        vwin.price_unit*sum(case when vwout.state='confirmed' then 0 else coalesce(vwout.quantity,0) end ) as allocated_amount,
                                        sum(case when vwout.state='confirmed' then coalesce(vwout.quantity,0) else 0 end ) as requesting_qty,
                                        vwin.quantity - sum(case when vwout.state!='confirmed' then coalesce(vwout.quantity,0) else 0 end ) as available_qty,
                                        vwin.price_unit * (vwin.quantity - sum(coalesce(vwout.quantity,0))) as remaining_amount
                                    from
                                        stock_location sl
                                    left join
                                        (-- STOCK IN
                                        --Stock In Local
                                            Select 
                                                sl.id as location_id,
                                                sm.product_id,
                                                sm.product_qty as quantity,
                                                sm.price_unit,
                                                sm.product_uom,
                                                sm.move_code,
                                                sm.source_move_code,
                                                sm.origin,
                                                sm.name as product_description,
                                                sm.state
                                            from
                                                stock_location sl
                                            left join
                                                stock_move sm on (sl.id = sm.location_dest_id) and sm.state in ('done','assigned') and sm.global_state <> 'done'
                                            where
                                                sl.global_stock and coalesce(sm.location_dest_id,0) != coalesce(sm.location_id,0) and coalesce(move_code,0)>0                                           
                                        Union
                                        --Stock In Remote
                                            Select 
                                                sl.id as location_id,
                                                pp.id as product_id,
                                                sm.product_qty as quantity,
                                                sm.price_unit,
                                                pu.id as product_uom,
                                                sm.move_code,
                                                sm.source_move_code,
                                                sm.origin,
                                                sm.product_description,
                                                sm.state
                                            from
                                                stock_location sl
                                            left join
                                                vwstock_move_remote sm on (sl.stock_code = stock_destination) and global_state <> 'done' and sm.state in ('done','assigned')
                                            left join
                                                product_product pp on product_code = pp.default_code
                                            left join
                                                product_uom pu on product_uom = pu.name
                                            where
                                                sl.global_stock and coalesce(move_code,0) > 0 and coalesce(stock_destination,'') != coalesce(stock_source, '')
                                           ) vwin on sl.id = vwin.location_id
                                    left join
                                        (-- STOCK Out
                                        --Stock Out Local
                                        Select 
                                                sl.id as location_id,
                                                sm.product_id,
                                                sm.product_qty as quantity,
                                                sm.price_unit,
                                                sm.product_uom,
                                                sm.move_code,
                                                sm.source_move_code,
                                                sm.origin,
                                                sm.name as product_description,
                                                sm.state
                                            from
                                                stock_location sl
                                            left join
                                                stock_move sm on (sl.id = sm.location_id) and sm.state in ('done','assigned','confirmed') and sm.global_state <> 'done'
                                            where
                                                sl.global_stock and coalesce(sm.location_dest_id,0) != coalesce(sm.location_id,0) and coalesce(source_move_code,0)>0
                                        Union
                                        --Stock Out Remote
                                            Select 
                                                sl.id as location_id,
                                                pp.id as product_id,
                                                sm.product_qty as quantity,
                                                sm.price_unit,
                                                pu.id as product_uom,
                                                sm.move_code,
                                                sm.source_move_code,
                                                sm.origin,
                                                sm.product_description,
                                                sm.state
                                            from
                                                stock_location sl
                                            left join
                                                vwstock_move_remote sm on (sl.stock_code = stock_source) and global_state <> 'done'
                                            left join
                                                product_product pp on product_code = pp.default_code
                                            left join
                                                product_uom pu on product_uom = pu.name
                                            where
                                                sl.global_stock and coalesce(source_move_code,0) > 0 and coalesce(stock_destination,'') != coalesce(stock_source, '')
                    ) vwout on vwin.location_id = vwout.location_id and vwin.move_code = vwout.source_move_code
                                    where
                                        coalesce(vwin.location_id,0)>0 or coalesce(vwout.location_id,0)>0 
                                    group by
                                        sl.id,
                                        vwin.location_id,
                                        vwin.quantity,    
                                        vwin.product_uom,
                                        vwin.move_code,
                                        vwin.source_move_code,
                                        vwin.origin,
                                        vwin.product_description,
                                        vwin.product_id,
                                        vwin.price_unit
                                    Order by
                                        sl.id""" % vwName)