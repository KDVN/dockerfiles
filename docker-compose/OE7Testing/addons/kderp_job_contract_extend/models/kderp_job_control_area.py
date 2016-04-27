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
import openerp.addons.decimal_precision as dp

from kderp_contract_job_area import CONTROL_TYPE_SELECTION

class kderp_job_control_area(osv.osv):
    _auto = False
    _name = "kderp.job.control.area"
    _description = """Job and Control Area"""

    _rec_name = 'area_id'
    _order = 'job_id, currency_id desc, control_support, area_id, amount desc'

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
        return list(set(result))

    _columns = {
                'control_support':fields.selection(CONTROL_TYPE_SELECTION, 'Area Type', required=True),
                'area_id':fields.many2one('kderp.control.area',"Area", required=True, ondelete="restrict"),
                'currency_id': fields.many2one('res.currency', 'Cur.', required=True, ondelete="restrict"),
                'area_per':fields.float("%", required=True, digits_compute=dp.get_precision('Amount')),
                'amount': fields.float("Amount", required=True, digits_compute=dp.get_precision('Amount')),
                'job_id':fields.many2one('account.analytic.account','Job', ondelete="restrict", required=True)
    }

    def init(self, cr):
        vwName = self.__class__.__name__
        sqlCheckTable = """SELECT 1
                                    FROM   pg_catalog.pg_class c
                                    JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                                    WHERE  n.nspname = 'public'
                                    AND    c.relname = '%s'
                                    AND    c.relkind = 'r'""" % vwName
        cr.execute(sqlCheckTable)
        if cr.fetchall():
            cr.execute("""DROP TABLE IF EXISTS %s""" % vwName)

        from openerp import tools

        tools.drop_view_if_exists(cr, vwName)
        cr.execute("""Create or replace view %s as
                    Select
                        row_number() Over (order by job_id, currency_id desc, control_support, area_id) as id,
                        job_id,
                        area_id,
                        currency_id,
                        sum(amount) as amount,
                        case when
                          coalesce(sum(sum(amount)) over (PARTITION BY job_id,currency_id),0)=0 then 0
                        else
                          sum(amount)/(sum(sum(amount)) over (PARTITION BY job_id,currency_id))*100.0 end as area_per,
                        control_support
                    from
                       kderp_contract_job_area kjca
                    Group by
                        job_id, area_id, currency_id, control_support
                    Order BY
                        job_id, currency_id desc, control_support, area_id""" % vwName)