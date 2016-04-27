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

from openerp.osv import fields, osv

class kderp_contract_client(osv.osv):
    _inherit = 'kderp.contract.client'
    _name = 'kderp.contract.client'

    def _check_area_per(self, cr, uid, ids):
        for ctc in self.browse(cr, uid, ids):
            job_amount_dict = {}
            job_area_amount_check = {}
            for kjq in ctc.contract_job_summary_ids:
                job_amount_dict[(kjq.account_analytic_id.code,kjq.currency_id.name)] = kjq.amount_currency
            for kca in ctc.contract_job_area_ids:
                key = (kca.job_id.code,kca.currency_id.name)
                if key not in job_amount_dict:
                    raise osv.except_osv("KDERP Warning", "Please check your Job %s (%s) not available in Job Info" % (key[0], key[1]))
                job_area_amount_check[key] = job_area_amount_check.get(key, 0) + kca.amount
            errors = []
            for key in job_area_amount_check:
                if job_area_amount_check[key] <> job_amount_dict[key]:
                    error = list(key)
                    error.append(("{:1,.2f} %s" % error[1]).format(job_amount_dict[key]))
                    errors.append((str(error[0]),str(error[2])))
            if errors:
                raise osv.except_osv("KDERP Warning","Please check Amount Job, Area %s " % (errors))
        return True

    _columns = {
                'contract_job_area_ids':fields.one2many('kderp.contract.job.area', 'contract_id', 'Job Control Area', readonly=True,states={'uncompleted':[('readonly',False)]}),
    }
    _constraints = [
        (_check_area_per, "KDERP Warning, Total of percentage AREA must equal to 100%", ['contract_job_area_ids'])]