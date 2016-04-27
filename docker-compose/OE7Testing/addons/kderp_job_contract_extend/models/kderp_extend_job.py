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

from openerp.osv import fields, osv

CONTROL_TYPE_SELECTION = (('control_area', 'Control Area'), ('support_area', 'Support Area'))

class kderp_job_control_area(osv.osv):
    _name = "kderp.job.control.area"
    _description = """Job and Control Area"""

    _rec_name = 'area_id'
    _order = 'control_support, area_id, area_per'

    def _get_area(self, cr, uid, ids, name, args, context = {}):
        res = {}
        for kjca in self.browse(cr, uid, ids):
            res[kjca.id] = kjca.area_per
        return res

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
                area_ids = self.search(cr, uid, [('control_support', 'ilike', name)] + args, limit=limit, context=context)
        else:
            area_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, area_ids, context=context)

    _columns = {
                'control_support':fields.selection(CONTROL_TYPE_SELECTION, 'Type', required=True),
                'area_id':fields.many2one('kderp.control.area',"Area", required=True, ondelete="restrict"),
                'area_per':fields.float("%", required=True),
                'area_progressbar':fields.function(_get_area, method =True, type='float', string=" "),
                'job_id':fields.many2one('account.analytic.account','Job', ondelete="restrict", required=True)
    }
    _sql_constraints = [("kderp_con_job_area_unique",'unique(job_id, area_id, support_type)', 'Type, Area must be unique')]
    _defaults = {
        'area_per': 0
    }

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'

    JOB_SCALE_SELECTION = [('big_job','Big Job'), ('small_maintenance', 'Small/Maintenance Job'), ('f-cost','F-Cost Job')]
    def _get_job_scale(self, cr, uid, ids, name, args, context = {}):
        res = {}
        for job in self.browse(cr, uid, ids):
            jobCode = job.code.upper()
            if jobCode[1:2] == 'A' or len(jobCode)<9: #Trong truong hop Job la HA hoac Code ko dung dinh dang
                res[job.id] = False
            elif len(jobCode)>10 and jobCode[10:11] == 'F':
                res[job.id] = 'f-cost'
            elif jobCode[4:6] == '-0':
                res[job.id] = 'big_job'
            elif jobCode[4:6] in ('-1','-2'):
                res[job.id] = 'small_maintenance'
        return res


    _columns={
                # 'control_area_id':fields.many2one('kderp.control.area','Control Area', ondelete='restrict'),
                # 'control_area_percent': fields.float('%'),
                # 'support_area_id': fields.many2one('kderp.control.area','Support Area', ondelete='restrict'),
                # 'support_area_percent': fields.float('%'),

                # FIXME Truong nay se co ten la Job Type, Job Type doi thanh E/M, phai hop nhat khi Upgrade len Odoo
                'job_scale':fields.function(_get_job_scale, type = 'selection', string = 'Job Type', selection = JOB_SCALE_SELECTION, method = True, select = 1,
                                            store = {'account.analytic.account':(lambda self, cr, uid, ids, context = {}: ids, ['code'], 50),}),

                'control_area_ids':fields.one2many('kderp.job.control.area', 'job_id', 'Control Area')
              }
account_analytic_account()
