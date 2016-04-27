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

class kderp_asset_report_wizard(osv.osv_memory):
    _name = 'kderp.asset.report.wizard'
    _description = 'KDERP Asset Report Wizard'
    _rec_name = 'state'
    
    def _get_status(self, cr, uid, context=None):
        asset_state = self.pool.get('kderp.asset.management').fields_get(cr, uid, ['state'],{})
        tmp_selection = asset_state['state']['selection']
        if ('all','All') not in tmp_selection:
            tmp_selection.append(('all','All'))
        return tuple(tmp_selection)        
    
    TYPE_OF_GROUP = [('current_user_id','User'),
                     ('asset_type_id','Asset Type'),
                     ('asset_code_id','Asset Code'),
                     ('current_job_id','Job'),
                     ('physical_location_id','Location')]
    _columns = {
        'state':fields.selection(TYPE_OF_GROUP,'Report A ', required=True),
        'file_type':fields.selection([('xls','Excel File'),('pdf','PDF File')],'File Type'),
        'current_user_id':fields.many2one('hr.employee','Select User',states={'current_user_id':[('invisible',False)]},invisible=1),
        'asset_code_id':fields.many2one('kderp.asset.code','Select Asset Code',states={'asset_code_id':[('invisible',False)]},invisible=1),
        'current_job_id':fields.many2one('kderp.job','Select Job',states={'current_job_id':[('invisible',False)]},invisible=1),
        'physical_location_id':fields.many2one('kderp.asset.location','Select Location',states={'physical_location_id':[('invisible',False)]},invisible=1),
        'asset_type_id':fields.many2one('kderp.type.of.asset','Asset Type',states={'asset_type_id':[('invisible',False)]},invisible=1),
        'status':fields.selection(_get_status,'Status',required=True)
    }
    _defaults = {
        'state': lambda *x: 'current_user_id',
        'status': lambda *x: 'inused',
        'file_type':'pdf'
    }
    
    def print_asset_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
            
        asset_report_data = self.read(cr, uid, ids, ['state','current_user_id','asset_code_id','current_job_id','physical_location_id','asset_type_id','status','file_type'])
        p_state = asset_report_data[0]['state']
        p_status = asset_report_data[0]['status']
        asset_obj=self.pool.get('kderp.asset.management')
        f_type=asset_report_data[0]['file_type'] if asset_report_data[0]['file_type'] else ' ' 
        
        asset_report_name={'asset_code_id':'kderp.asset.report.item',
                           'current_user_id':'kderp.asset.report.user',
                           'current_job_id':'kderp.asset.report.job',
                           'physical_location_id':'kderp.asset.report.location',
                           'asset_type_id':'kderp.asset.report.type'}            
        
        title='Asset Report - %s' % dict(self.TYPE_OF_GROUP)[p_state]
        
        id_search = asset_report_data[0][p_state][0]
        if p_state!='asset_type_id':
            asset_domain=[(p_state,'=',id_search)]
        else:
            asset_domain=[('type_asset_acc_id.typeofasset_id','=',id_search)]
            
        if p_status!='all':
            asset_domain.extend([('state','=',p_status)])
            
        asset_ids = asset_obj.search(cr, uid, asset_domain)
        data={'ids':asset_ids,
              'model':'kderp.asset.management', 'title' : title}
        
        return {'type': 'ir.actions.report.xml', 'report_name': asset_report_name[p_state]+f_type.replace('pdf','').replace('xls','.xls').strip(), 'datas': data}    

kderp_asset_report_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
