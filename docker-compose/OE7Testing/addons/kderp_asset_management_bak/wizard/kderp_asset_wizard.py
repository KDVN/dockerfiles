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

from lxml import etree

from openerp import tools
from openerp.tools.translate import _
from openerp.osv import fields, osv

class kderp_asset_update_job(osv.osv_memory):
    _name = 'kderp.asset.update.job'
    _description = 'Update Job for Asset List'

    _columns = {
    }

    def update_job(self, cr, uid, ids, context=None):
        res=self.pool.get('kderp.job').update_job(cr, uid, ids)
        return True

kderp_asset_update_job()

class kderp_create_sub_asset(osv.osv_memory):
    _name = 'kderp.create.sub.asset'
    _description = 'KDERP Create Sub Asset'

    _columns = {
                'quantity_to_create':fields.integer('Quantity',required=True)
                }

    _defaults={
        'quantity_to_create': lambda self, cr, uid, context: self._get_quantity(cr, uid, context)
    }   
    def create_sub_asset(self, cr, uid, ids, context={}):
        state='draft'
        quantity=self.read(cr, uid, ids,['quantity_to_create'])[0]['quantity_to_create']
        list_ids=[]
        asset_id=context.get('active_id',False) 
        if asset_id:
            asset_obj=self.pool.get('kderp.asset.management')
            ass_list=asset_obj.copy_data(cr, uid, asset_id)
            ass_list['asset_ids']=[]
            ass_list['related_asset_ids']=[]
            #a=ass_list.pop('asset_usage_ids') if 'asset_usage_ids' in ass_list else False
            a=ass_list.pop('sub_asset_ids') if 'sub_asset_ids' in ass_list else False
            ass_list['state']=state
            asset_code=ass_list['code']
            for sub in range(1,quantity+1):
                ass_list['code']=asset_code + "-" + str(sub).zfill(3)   
                ass_list['parent_id']=asset_id
                ass_list['quantity']=1
#                list_to_create.append(ass_list)
                list_ids.append(asset_obj.create(cr, uid, ass_list))
        return list_ids
    
    def _get_quantity(self, cr, uid, context=None):
        if 'active_id' in context:
            return self.pool.get('kderp.asset.management').browse(cr, uid, context['active_id'], context).quantity
        
kderp_create_sub_asset()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
