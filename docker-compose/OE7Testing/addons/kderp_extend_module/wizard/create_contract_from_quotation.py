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

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class kderp_quotation_contract(osv.osv_memory):
    """KDERP Quotation Contract"""

    _name = "kderp.quotation.contract"
    _inherit = "kderp.quotation.contract" 
    _description = "KDERP Quotation Contract"    
        
    _columns = {
                'project_location_id':fields.many2one('kderp.location','Project Location',required=True),
                'city_province_id': fields.many2one('kderp.city', 'City Province'),
               }

    def onchange_location_city(self, cr, uid, ids, project_location_id=False):
        if not project_location_id:
            return {'value': {
                'city_province_id': False,
            }}
        location = self.pool.get('kderp.location').browse(cr, uid, project_location_id)
        city_province_id = False
        if location and location and location.city_id:
            city_province_id = location.city_id.id
        return {'value': {
            'city_province_id': city_province_id
        }}

    def create_contract_and_update(self, cr, uid, id, context):
        if not context:
            context={}
        new_form_data = self.read(cr,uid,id,['contract_code_new','contract_name_new','contract_code_exist','project_location_id','city_province_id'],context)
        sale_obj = self.pool.get('sale.order')
        kderp_ctc_obj = self.pool.get('kderp.contract.client')
        if new_form_data[0]['contract_code_exist']:
            contract_exist_code=new_form_data[0]['contract_code_exist']
            contract_id=kderp_ctc_obj.search(cr,uid,[('code','=',contract_exist_code)])[0]
        else:
            for so in sale_obj.browse(cr,uid,[context.get('order_id',False)]):                
                client_id = so.partner_id.id
                owner_id = so.owner_id.id
                project_name = so.project_name
                address_id = so.partner_address_id.id
                invoice_address_id = so.partner_invoice_id.id
                project_location_id = new_form_data[0]['project_location_id'][0]
                city_province_id = new_form_data[0]['city_province_id'][0] if new_form_data[0]['city_province_id'] else False
                tax_ids = []
                curr_ids = []
                
                for curr in so.summary_quotation_ids:
                    curr_ids.append({'curr_id':curr.currency_id.id,'tax_ids':[],'curr_name':curr.currency_id.name,'default_curr':True})
                    
                for sol in so.quotation_submit_line:
#                     if sol.currency_id.name in [x['curr_name'] for x in curr_ids]:
                    tax_ids_sub = []
                    for tax in sol.tax_id:
                        tax_ids_sub.append(tax.id)
                    tax_ids.append({'curr_id':sol.currency_id.id,'curr_name':sol.currency_id.name,'tax_ids':tax_ids_sub,'default_curr':True})
                
                contract_code=new_form_data[0]['contract_code_new']
                contract_name=new_form_data[0]['contract_name_new']
                
                new_e_vals={"code":contract_code,"name":contract_name,
                            'owner_id':owner_id,
                            'client_id':client_id,'address_id':address_id,'invoice_address_id':invoice_address_id,
                            'project_name':project_name,'date':time.strftime("%Y-%m-%d"),
                            'project_location_id': project_location_id,
                            'city_province_id': city_province_id}
                
                ctx={'curr_tax_ids':tax_ids if tax_ids else curr_ids}
                
                contract_id=kderp_ctc_obj.create(cr,uid,new_e_vals,ctx)
                ctx['contract_id']=contract_id
                
        if contract_id:   
            sale_obj.write(cr,uid,context.get('order_id',False),{'contract_id':contract_id})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Contract',
                'view_type': 'form',
                'res_id':contract_id,
                'target':'current',
                'nodestroy': True,
                'view_mode': 'form,tree',
                'res_model': 'kderp.contract.client',
                'domain': "[('id','=',%s)]" % contract_id
                }
        return True
kderp_quotation_contract()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
