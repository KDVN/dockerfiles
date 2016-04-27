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


class res_currency(osv.osv):
    _inherit = 'res.currency'

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        if args is None:
            args = []
        if context is None:
            context = {}
        if context.get("filter_by_contract_id", False):
            contract_id = context.get("filter_by_contract_id", False)
            sqlConn = """Select DISTINCT currency_id from kderp_quotation_contract_project_line kqcpl where contract_id=%s""" % contract_id
            cr.execute(sqlConn)
            curr_ids = [curr_id[0] for curr_id in cr.fetchall()]
            args.append(('id', 'in', curr_ids))
        return super(res_currency, self).name_search(cr, user, name, args=args, operator='ilike', context=None, limit=80)