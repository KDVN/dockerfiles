# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import openerp.addons.decimal_precision as dp

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class sale_order(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'
    _description = 'Quotation'   
       
    def _get_quotation_attachment(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if ids:
            so_id_list = ",".join(map(str,ids))
            cr.execute("""Select
                           so.id as id,
                           case when sum(case when coalesce(ia.quotation_budget_na,False) then 1 else 0 end) >0 then 1 else 0 end as quotation_budget_na,
                           case when sum(case when coalesce(ia.quotation_job_budget_na,False) then 1 else 0 end) >0 then 1 else 0 end as quotation_job_budget_na
                       from
                           sale_order so
                       left join
                           ir_attachment ia on so.id=ia.res_id and res_model='sale.order'
                       where
                           so.id in (%s) 
                       group by 
                            so.id""" % (so_id_list))
            for sol in cr.dictfetchall():
                res[sol.pop('id')]=sol
        return res
    
    def _get_attachement_link(self, cr, uid, ids, context=None):
        res={}
        for att_obj in self.pool.get('ir.attachment').browse(cr,uid,ids):
            if att_obj.res_model=='sale.order' and att_obj.res_id:
                res[att_obj.res_id] = True
        return res.keys()    
        
    def _get_quotation_id_from_approved_line(self, cr, uid, ids, context=None):
        res=[]
        for sol in self.pool.get('sale.order.line').browse(cr,uid,ids):
            res.append(sol.order_id.id)
        return res
    def _get_sort_approved_amount(self, cr, uid, ids, name, arg, context=None):
        res={}
        if ids:
            so_ids=','.join(map(str,ids))
            cr.execute("""Select 
                            so.id,
                            min(case when coalesce(sol.id,0)>0 and coalesce(sol.price_unit,0)=0 then 2 else 1 end)
                        from 
                            sale_order so
                        left join
                            sale_order_line sol on so.id=sol.order_id
                        where
                            so.id in (%s)
                        group by 
                            so.id""" % so_ids)
            for so_id,re in cr.fetchall():
                res[so_id]=re
        return res
    
    _columns={
              'project_location_id':fields.many2one('kderp.location','Project Location', ondelete='restrict'),
              
              'sort_approved_amount':fields.function(_get_sort_approved_amount,method=True,string="Sort",type='integer',
                                            store={
                                                   'sale.order':(lambda self, cr, uid, ids, c={}: ids, None, 20),
                                                   'sale.order.line':(_get_quotation_id_from_approved_line,None,35),
                                                   }),
              
               'quotation_budget_na':fields.function(_get_quotation_attachment,method=True,string='Quotation Budget N/A',readonly=True,type='boolean',multi='quotation_attachment_budget_na',
                                             store={
                                                    'sale.order':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','quotation_budget_na','quotation_job_budget_na'],20)}),
               'quotation_job_budget_na':fields.function(_get_quotation_attachment,method=True,string='Job Budget N/A',readonly=True,type='boolean',multi='quotation_attachment_budget_na',
                                             store={
                                                    'sale.order':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','quotation_budget_na','quotation_job_budget_na'],20)}),
                # Them 2 lien ket moi vao quotation
                'kderp_quotation_temporary_line':fields.one2many('kderp.quotation.temporary','order_id','Temporary Quotation Electrical',context={'job_type':'E'},domain=[('job_type','=','E')]),
                'kderp_quotation_temporary_line_m':fields.one2many('kderp.quotation.temporary','order_id','Temporary Quotation Mechanical',context={'job_type':'M'},domain=[('job_type','=','M')]),
                
                # Add new 2 fields Working Budget Availability Electrical & Mechanical
                'wb_availability_e':fields.boolean('W.B. N/A (E)'),
                'wb_availability_m':fields.boolean('W.B. N/A (M)')             
              }
    _defaults ={
                'wb_availability_e':False,
                'wb_availability_m':False
                }
sale_order()

# Them bang moi Quotation Temporary
class kderp_quotation_temporary(osv.osv):
    _name='kderp.quotation.temporary'    
    _description='Detail Quotation Temporary'
    
    def _get_job_type(self,cr,uid,context={}):
        if not context:
            context={}
        return context.get('job_type',False)
    
    _columns={
                'name':fields.char('Description',size=250),
                'currency_id':fields.many2one('res.currency','Cur.',required=True),
                'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
                'discount':fields.float('Discount',required=True),
                'order_id': fields.many2one('sale.order', 'Quotation', required=True, ondelete='restrict', select=True),
                'job_type':fields.selection([('E','Electrical'),('M','Mechanical')],'Type',required=True),
              }
    _sql_constraints=[('kderp_breakdown_temporary_currency','unique(currency_id,order_id,job_type)','Currency for Temporary Breakdown must be unique !')]
    _order = 'order_id desc'
    _defaults = {
                 'discount':0.0,
                 'job_type':_get_job_type,
                 }
kderp_quotation_temporary()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

