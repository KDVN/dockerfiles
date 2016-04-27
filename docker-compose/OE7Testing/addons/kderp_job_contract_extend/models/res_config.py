# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
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
from openerp import pooler
from openerp.tools.translate import _

class kderp_job_contract_config(osv.osv_memory):
    _name = 'kderp.job.contract.config'
    _inherit = 'res.config.settings'

    _columns = {
        'group_control_area_for_job': fields.boolean('Control Area In Job',
            implied_group='kderp_job_contract_extend.group_kderp_control_area_job_show_view',
            help="Allows you to specify Area(s) on Job."),
        'group_control_area_for_contract': fields.boolean('Control Area In Contract',
                                                     implied_group='kderp_job_contract_extend.group_kderp_control_area_contract_show_view',
                                                     help="Allows you to show Area in Contract (link from Job)."),
    }

    def onchange_group_control_for_job(self, cr, uid, ids, group_area_job, context=None):
        """ change group_control_area_for_job following group_control_area_for_contract """
        val = {}
        if not group_area_job:
            val = {'group_control_area_for_contract': False}
        return {'value': val}

    def onchange_group_control_area_for_contract(self, cr, uid, ids, group_area_contract, context=None):
            """ change group_control_area_for_job following group_control_area_for_contract """
            val = {}
            if group_area_contract:
                val = {'group_control_area_for_job': True}
            return {'value': val}