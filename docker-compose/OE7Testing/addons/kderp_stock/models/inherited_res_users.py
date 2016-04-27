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

class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}

        if context.get('filter_storekeeper', False):
            strSQL = """Select DISTINCT ru.id from res_users ru left join resource_resource rr on ru.id = rr.user_id left join hr_employee hr on rr.id=resource_id left join hr_department hd on department_id =  hd.id where hd.code='S1420'"""
            cr.execute(strSQL)
            user_ids = [ruids[0] for ruids in cr.fetchall()]
            args.append((('id', 'in', user_ids)))
        return super(res_users, self).search(cr, user, args, offset=0, limit=None, order=None, context=None, count=False)

res_users()
