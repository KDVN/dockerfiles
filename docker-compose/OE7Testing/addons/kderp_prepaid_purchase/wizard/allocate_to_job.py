# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP SA (<http://openerp.com>).
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
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

class kderp_order_allocate_to_job_select(osv.osv_memory):
    _name = "kderp.order.allocate.to.job.select"
    _rec_name = 'prepaid_ref'
    _description = "Allocated Stock Order to Job"
    
    def _get_prepaid_order(self, cr, uid, context):        
        stock_location_id = context.get('location_id', 0)
        if stock_location_id:        
            cr.execute("""Select                                    
                                origin
                            from
                                stock_location sl
                            left join
                                stock_move sm on sl.id = sm.location_dest_id and state = 'done' and sm.global_state <> 'done'
                            where
                                sl.global_stock and coalesce(sm.location_dest_id,0) != coalesce(sm.location_id,0) and sm.move_code is not null and sl.id = %s
                            Union
                            Select                                    
                               origin
                            from
                                stock_location sl
                            left join
                                vwstock_move_remote sm on sl.stock_code = sm.stock_destination and sm.global_state <> 'done'
                            where
                                sl.global_stock and coalesce(sm.stock_destination,'') != coalesce(sm.stock_source,'') and sm.move_code is not null and sl.id = %s""" % (stock_location_id, stock_location_id))
        res = []
        for ppo_no in cr.fetchall():
            code = str(ppo_no[0])
            res.append((code, code))
        return res
    
    _columns = {
                'prepaid_ref':fields.selection(_get_prepaid_order,'Prepaid Ref.', required = True)
                }
    
    def open_stock_allocated(self, cr, uid, ids, context):
        if not context:
            context = {}
        context['origin'] = self.browse(cr, uid, id, context).prepaid_ref
        return {
            'type': 'ir.actions.act_window',
            'res_model':'kderp.stock.order.allocate.to.job',
            'name': _('Allocate to Job'),
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
    
class kderp_stock_move_allocate_to_job_line(osv.TransientModel):

    _name = "kderp.stock.move.allocate.to.job.line"
    _rec_name = 'product_id'
    _columns = {        
        'product_id':fields.many2one('product.product','Product', required = True, readonly = True),
        'product_uom':fields.many2one('product.uom', 'Unit', required = True, digits=(16,2), readonly = True),
        'product_qty':fields.float("Quantity", required = True),
        'available_qty':fields.float("Avail. Qty.", required = True, readonly = True),
        'price_unit':fields.float('Price Unit', required = True, readonly = True, digits_compute=dp.get_precision('Amount')),
        'name':fields.char('Description', required = True, size = 128, readonly = True),
        #'location_id':fields.many2one('stock.location', 'Source', required = True, domain = [('usage','=','internal')]),
        'location_dest_id':fields.many2one('stock.location', 'To Stock', domain = [('usage','=','internal')]),
        'move_code':fields.float('Move Code', readonly = True),
        'wizard_id' : fields.many2one('kderp.stock.order.allocate.to.job', string="Wizard", ondelete='CASCADE', readonly = True),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Job', ondelete='CASCADE'),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, name, qty, uom_id, price_unit, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
  
        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
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

class kderp_stock_to_order_allocate_to_job(osv.osv_memory):
    _name = "kderp.stock.order.allocate.to.job"
    _rec_name = 'date'
    _description = "Allocated Stock Order to Job"

    _columns = {
        'date': fields.datetime('Date', required=True),
        'stock_location_id':fields.many2one('stock.location', 'From Stock', readonly = 1),
        'location_dest_id':fields.many2one('stock.location', 'To Stock', required = True, domain = [('usage','=','internal')]),
        'description':fields.char('Description', size=128, required = True),
        'origin':fields.char('Origin', readonly = 1),
        'partner_id':fields.many2one('res.partner', 'Supplier', ondelete='restrict', required=True),
        'address_id':fields.many2one('res.partner', 'Address', ondelete='restrict'),
        'product_details' : fields.one2many('kderp.stock.move.allocate.to.job.line', 'wizard_id', 'Product Moves'),
        'account_analytic_id': fields.many2one('account.analytic.account', 'Job', required=True, ondelete='CASCADE'),
    }
    
    def _allocate_line_for(self, cr, uid, pd, context=None):
        pol = {
            'product_id': pd.product_id.id,
            'price_unit':pd.price_unit if pd.price_unit else False,
            'product_uom':pd.product_uom.id,
            'available_qty':pd.available_qty,
            'product_qty': pd.available_qty if pd.available_qty==1 else False,
            'name': pd.product_description,
            'product_uom': pd.product_uom.id,
            'move_code': pd.move_code
        }
        return pol
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(kderp_stock_to_order_allocate_to_job, self).default_get(cr, uid, fields, context=context)
        stock_location_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not stock_location_ids or len(stock_location_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.location'), 'Bad context propagation'        
        stock_location_id, = stock_location_ids

        stl = self.pool.get(active_model).browse(cr, uid, stock_location_id, context=context)
        #vat_code = False
#         for pd in stl.product_details:
#             if pd.vat_code:
#                 vat_code = pd.vat_code
#                 break
        #cr.execute("""Select vat_code from stock_location_product_detail where location_id=%s and coalesce(vat_code,'')<>'' limit 1""" % stock_location_id)
        #if cr.rowcount:
        #    vat_code = cr.fetchone()[0]
        
        if 'partner_id':
            partner_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.id            
            res.update(partner_id=partner_id)        
            res.update(address_id=partner_id)
        res.update(origin=context.get('origin', ''))
        if 'description' in fields:
            res.update(description='Allocated material from stock to Job')        
        if 'stock_location_id' in fields:
            res.update(stock_location_id=stock_location_id)
        if 'location_dest_id' in fields:
            dest_loc_ids = self.pool.get('stock.location').search(cr, uid, [('default_project_stock','=',True)])
            res.update(location_dest_id=dest_loc_ids[0] if dest_loc_ids  else False)
        if 'product_details' in fields:
            ppo_lines = [self._allocate_line_for(cr, uid, pd, context=context) for pd in stl.product_details if pd.origin == context.get('prepaid_ref','') and pd.available_qty>0]
            res.update(product_details=ppo_lines)
        if 'date' in fields:
            res.update(date=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
        return res

    def _create_poline(self, wizard_obj_line, wizard_obj, seq):
        return (0, False, {
            'account_analytic_id': wizard_obj_line.account_analytic_id.id if wizard_obj_line.account_analytic_id else wizard_obj.account_analytic_id.id,
            'plan_qty': wizard_obj_line.product_qty,            
            'product_id': wizard_obj_line.product_id.id,
            'product_uom': wizard_obj_line.product_uom.id,
            'price_unit': wizard_obj_line.price_unit,
            'name': wizard_obj_line.name,            
            'move_code': wizard_obj_line.move_code,
            'location_id': wizard_obj.stock_location_id.id,
            'location_dest_id': wizard_obj_line.location_dest_id.id if wizard_obj_line.location_dest_id.id else wizard_obj.location_dest_id.id,
            'sequence': seq
        })

    def create_po(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        assert len(ids) == 1, 'Allocate to Job processing may only be done one at a time.'
        #stock_picking = self.pool.get('stock.picking')
        stock_move = self.pool.get('stock.move')
        #uom_obj = self.pool.get('product.uom')
        po_obj = self.pool.get('purchase.order')
        allocateJob = self.browse(cr, uid, ids[0], context=context)
        job_id = allocateJob.account_analytic_id.id
        
        curr_name = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.name
        pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [('name','=',curr_name)])
        pricelist_id = pricelist_ids[0] if pricelist_ids else False
        
        po_data = po_obj.default_get(cr, uid, context)
        po_data.update({
            'date_order': time.strftime('%Y-%m-%d'),
            'partner_id': allocateJob.partner_id.id,
            'address_id': allocateJob.address_id.id if allocateJob.address_id else allocateJob.partner_id.id,
            'pricelist_id': pricelist_id,
            'notes': allocateJob.description,
            'typeoforder': 'm',
            'account_analytic_id': job_id,
            'name': po_obj.new_code(cr, uid, False, job_id, 'm')['value']['name'],
            'allocate_order': True,
            'origin': allocateJob.origin,
            'invoice_method':'picking'
        })
        
        pols = []
        seq = 0
        for wizard_line in allocateJob.product_details:
            #quantity must be Positive
            if wizard_line.available_qty - wizard_line.product_qty < 0:
                raise osv.except_osv(_('Warning!'), _('Please check Quantity.'))
            #Skip line if allocated qty = 0
            if wizard_line.product_qty == 0:
                continue

            #Compute the quantity for respective wizard_line in the line uom (this jsut do the rounding if necessary)
            #qty_in_line_uom = uom_obj._compute_qty(cr, uid, line_uom.id, wizard_line.quantity, line_uom.id)

            #if line_uom.factor and line_uom.factor <> 0:
            #    if float_compare(qty_in_line_uom, wizard_line.quantity, precision_rounding=line_uom.rounding) != 0:
            #        raise osv.except_osv(_('Warning!'), _('The unit of measure rounding does not allow you to ship "%s %s", only rounding of "%s %s" is accepted by the Unit of Measure.') % (wizard_line.quantity, line_uom.name, line_uom.rounding, line_uom.name))
            seq += 1
            pols.append(self._create_poline(wizard_line, allocateJob, seq))
        if not pols:
            return {'type': 'ir.actions.act_window_close'}
        po_data.update(order_line=pols)
        po_id = po_obj.create(cr, uid, po_data, context)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'name': _('Purchase'),
            'res_id': po_id,
            'view_type': 'form',
            'view_mode': 'form,tree',
            'context': context,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
