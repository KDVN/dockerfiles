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

class wizard_kderp_job_list_ongoing(osv.osv_memory):
    _name = 'wizard.kderp.job.list.ongoing'
    _description = 'Job Wizard Job List On Going'
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        jwbs = self.browse(cr, uid, ids[0])
        datas = {'ids': context.get('active_ids',[])}


        context['from_date'] = jwbs.from_date
        context['to_date'] = jwbs.to_date

        datas['model'] = 'account.analytic.account'
        datas['title'] = '10.1 List of Job On-Going'
        
        report_name= "kderp.report.list.of.job.on.going.xls"
          
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
            'context': context
            }

    _columns = {                
                'from_date':fields.date('From Date'),
                'to_date': fields.date('To Date')
                }
wizard_kderp_job_list_ongoing()