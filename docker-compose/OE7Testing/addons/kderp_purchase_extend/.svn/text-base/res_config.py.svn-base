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

class kderp_po_expense_config_settings(osv.osv_memory):
    _name = 'kderp.po.expense.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
                'other_expense_payment_voucher_prepared_user_id': fields.many2one('hr.employee','Prepared User',required=True, help='User appear in payment voucher in Supplier Payment Expense'),
                'po_payment_voucher_prepared_user_id': fields.many2one('hr.employee','Prepared User',required=True, help='User appear in payment voucher in Supplier Payment'),
    }
    
    def set_other_expense_payment_voucher_prepared_user_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({'other_expense_payment_voucher_prepared_user_id': config.other_expense_payment_voucher_prepared_user_id.id,
                               })
        
    def set_po_payment_voucher_prepared_user_id(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        user.company_id.write({
                               'po_payment_voucher_prepared_user_id':config.po_payment_voucher_prepared_user_id.id
                               })
    _defaults = {
        'other_expense_payment_voucher_prepared_user_id': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.other_expense_payment_voucher_prepared_user_id.id,
        'po_payment_voucher_prepared_user_id': lambda self, cr, uid, context:self.pool.get('res.users').browse(cr, uid, uid, context).company_id.po_payment_voucher_prepared_user_id.id
        }
        
class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    
    _columns = {
                'other_expense_payment_voucher_prepared_user_id': fields.many2one('hr.employee','Prepared User',required=True, help='User appear in payment voucher in Supplier Payment Expense'),
                'po_payment_voucher_prepared_user_id': fields.many2one('hr.employee','Prepared User',required=True, help='User appear in payment voucher in Supplier Payment'),       
                }