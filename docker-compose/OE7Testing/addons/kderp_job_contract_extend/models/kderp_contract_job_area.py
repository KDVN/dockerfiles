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

CONTROL_TYPE_SELECTION = (('control_area', 'Control Area'), ('support_area', 'Support Area'))

import openerp.addons.decimal_precision as dp

class kderp_contract_job_area(osv.osv):
    _name = 'kderp.contract.job.area'
    _description = 'KDERP Contract & Job Control Area Percentage'
    _rec_name = "job_id"
    _order = 'contract_id, job_id, control_support, currency_id, amount desc'

    #Field Function Area
    def _get_area_job_per(self, cr, uid, ids, name, args, context):
        res = {}
        for kca in self.browse(cr, uid, ids):
            job_id = kca.job_id.id
            curr_id = kca.currency_id.id
            kca_amount = kca.amount
            total_amount = 0
            for kqcpl in kca.contract_id.contract_job_summary_ids:
                if kqcpl.account_analytic_id.id == job_id and kqcpl.currency_id.id == curr_id:
                    total_amount = kqcpl.amount_currency
            res[kca.id] = (kca_amount/total_amount*100) if total_amount else 0
        return res

    #Area for Function get IDS
    def _get_ids_from_contract(self, cr, uid, ids, context):
        res = {}
        for ctc in self.pool.get('kderp.contract.client').browse(cr, uid, ids):
            for kca in ctc.contract_job_area_ids:
                res[kca.id] = True
        return res.keys()

    def _get_ids_from_contract_job(self, cr, uid, ids, context):
        res = {}
        for kqcpl in self.pool.get('kderp.quotation.contract.project.line').browse(cr, uid, ids):
            for kca in kqcpl.contract_id.contract_job_area_ids:
                res[kca.id] = True
        return res.keys()

    #Default value Area - Function for get Default Value
    def _get_job_id(self, cr, uid, context):
        context = context or {}
        ctc_id = context.get('contract_id', False)
        if ctc_id:
            job_ids = []
            ctc = self.pool.get('kderp.contract.client').browse(cr, uid, ctc_id)
            for jcl in ctc.contract_job_summary_ids:
                job_ids.append(jcl.account_analytic_id.id)
            job_ids = list(set(job_ids))
            return False if len(job_ids)<>1 else job_ids[0]
        else:
            raise osv.except_osv("KDERP Warning", "You can't create Contract and Job Control Area, please create contract first")

    def _get_curr_id(self, cr, uid, context):
        context = context or {}
        ctc_id = context.get('contract_id', False)
        if ctc_id:
            curr_ids = []
            ctc = self.pool.get('kderp.contract.client').browse(cr, uid, ctc_id)
            for jcl in ctc.contract_job_summary_ids:
                curr_ids.append(jcl.currency_id.id)
            curr_ids = list(set(curr_ids))
            return False if len(curr_ids) <> 1 else curr_ids[0]
        else:
            raise osv.except_osv("KDERP Warning",
                                 "You can't create Contract and Job Control Area, please create contract first")

    _columns={
                'contract_id':fields.many2one('kderp.contract.client','Contract', required=True, ondelete="restrict"),
                'job_id': fields.many2one('account.analytic.account', 'Job', required=True, ondelete="restrict"),
                'area_id':fields.many2one('kderp.control.area',"Area", required=True, ondelete="restrict"),
                'currency_id': fields.many2one('res.currency', 'Cur.', required=True, ondelete="restrict"),
                'control_support':fields.selection(CONTROL_TYPE_SELECTION, 'Area Type', required=True),
                'amount': fields.float("Amount", required=True, digits_compute=dp.get_precision('Amount')),
                'area_per':fields.function(_get_area_job_per, type='float', method=True, string="%",digits_compute=dp.get_precision('Amount'),
                                           store={
                                               'kderp.contract.job.area': (lambda self, cr, uid, ids, context={}: ids, ['amount','job_id'], 10),
                                               'kderp.contract.client': (_get_ids_from_contract, ['contract_job_summary_ids'], 10),
                                               'kderp.quotation.contract.project.line':(_get_ids_from_contract_job, None, 10),
                                           })
              }
    _defaults = {
                'job_id':_get_job_id,
                'currency_id':_get_curr_id,
    }

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}

        if name:
            name = name.strip()
            area_ids = self.search(cr, uid, [('area_id', '=', name)] + args, limit=limit, context=context)
            if not area_ids:
                area_ids = self.search(cr, uid, [('area_id', 'ilike', name)] + args, limit=limit, context=context)
            if not area_ids:
                area_ids = self.search(cr, uid, [('control_support', '=', name)] + args, limit=limit, context=context)
            if not area_ids:
                area_ids = self.search(cr, uid, [('control_support', 'ilike', name)] + args, limit=limit,
                                       context=context)
        else:
            area_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, area_ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        context = context or {}
        result = []
        for var in self.browse(cr, uid, ids, context=context):
            if context.get('code_only', False):
                res = (var.id, var.area_id.code)
            elif context.get('name_only', False):
                res = (var.id, var.area_id.name)
            else:
                res = (var.id, "%s - %s" % (var.area_id.code, var.area_id.name))
            result.append(res)
        return result