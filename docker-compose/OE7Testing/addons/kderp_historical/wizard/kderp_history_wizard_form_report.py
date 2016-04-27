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
from datetime import timedelta, date
from openerp.osv import fields, osv

class kderp_historical_data_wizard_form(osv.osv_memory):
    _name = 'kderp.historical.data.wizard.form'
    _description = 'Historical Data Wizard Print Report'

    def print_report(self, cr, uid, ids, data, context=None):
        cr.execute("Select pol.id from purchase_order_line pol limit 10")
        kderphd_ids = []
        for idss in cr.fetchall():
            kderphd_ids.append(idss[0])

        data['ids'] = kderphd_ids
        data['id'] = kderphd_ids[0]

        if context is None:
            context = {}
        hd = self.browse(cr, uid, ids[0])
        datas = {'ids': kderphd_ids,
                 'parameters': {
						'pdate_start': hd.pdate_start,
						'pdate_end': hd.pdate_end
					}
                }

        datas['model'] = 'purchase.order.line'
        datas['title'] = 'Historical Form'

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'kderp.report.historical.data.%s' % hd.file_type,
            'datas': datas
        }

    _columns = {
        'pdate_start': fields.date('Start Date'),
        'pdate_end': fields.date('End Date'),
        'file_type': fields.selection([('xls', 'Excel File'), ('pdf', 'PDF File')], 'File Type', required=1),
    }
    _defaults = {
        'pdate_start': (date.today() - timedelta(days=date.today().day)).strftime("%Y-%m-10"),
        'pdate_end': date.today().strftime("%Y-%m-10"),
        'file_type': 'xls',
    }
kderp_historical_data_wizard_form()