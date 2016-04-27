#-*- coding: utf-8 -*-
###############################################################################
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
from osv import fields, osv
from openerp import SUPERUSER_ID

class kderp_wizard_create_stock(osv.osv_memory):
    _name='kderp.wizard.create.stock'
    _description='Create Stock(warehouse) Wizard'

    _columns = {
                'job_ids':fields.many2many('account.analytic.account', 'account_analytic_wizard_create_stock_rel',
                                           'analytic_account_id','stock_id', 'Job(s)', required=True, domain=[('state','not in',('closed','cancel')),('general_expense','=',False)]),
                'storekeeper_ids':fields.many2many('res.users', 'wizard_create_stock_storekeeper_user_rel', 'stock_id', 'user_id', 'Storekeepers',
                                                   ondelete='restrict', context={'filter_storekeeper': True}),
                }

    #Tao Stock
    def action_create_stock(self, cr, uid, ids, context):
        stock_ids = []
        # Create Stock Related Project
        context = context or {}
        ctx = context.copy()
        for kwcs in self.browse(cr, uid, ids):
            sl_obj = self.pool.get('stock.location')
            user_ids = [ru.id for ru in kwcs.storekeeper_ids]
            for job in kwcs.job_ids:
                ctx['jobCode'] = job.code
                ctx['warehouseType'] = 'internal'

                stock_vals = {'name': job.name,
                              'account_analytic_id': job.id,
                              'usage': 'internal',
                              'storekeeper_ids': [(6, False, user_ids)]
                              }
                stk_id = sl_obj.create(cr, SUPERUSER_ID, stock_vals, ctx)
                stock_ids.append(stk_id)
                stock_vals['usage'] = 'customer'
                ctx['warehouseType'] = 'customer'
                stk_id = sl_obj.create(cr, SUPERUSER_ID, stock_vals, ctx)
                stock_ids.append(stk_id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Warehouse(s)',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.location',
            'domain': "[('id','in', ["+','.join(map(str, stock_ids))+"])]"
            }