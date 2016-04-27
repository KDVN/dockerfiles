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

import time
from lxml import etree
import openerp.addons.decimal_precision as dp

from openerp import netsvc
from openerp import pooler
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = 'purchase.order'
    _description = "KDERP Purchase Order"
        
    
    
    _columns={
              'total_request_amount':fields.function(_get_summary_payment_amount,string='Requested Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              'total_vat_amount':fields.function(_get_summary_payment_amount,string='Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 25),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'subtotal_vat_amount':fields.function(_get_summary_payment_amount,string='Sub-Total Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 30),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'vat_amount':fields.function(_get_summary_payment_amount,string='VAT Invoice Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order'], 20),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','kderp_vat_invoice_ids'], 30),
                                                              'kderp.supplier.vat.invoice': (_get_order_from_supplier_vat, None, 30),
                                                             }),
              'total_payment_amount':fields.function(_get_summary_payment_amount,string='Payment Amt.',
                                                       method=True,type='float',multi="_get_summary",
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order'], 5),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['state','order_id'], 10),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             }),
              
              'payment_percentage':fields.function(_get_summary_payment_amount,string='Payment Percentage',
                                                       method=True,type='float',multi="_get_summary",digits_compute=dp.get_precision('Percent'),
                                                       store={
                                                              'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['pricelist_id','date_order','allocate_order','discount_amount','taxes_id'], 20),
                                                              'purchase.order.line': (_get_order_from_line, None, 10),
                                                              'kderp.supplier.payment': (_get_order_from_supplier_payment, ['order_id','state','amount','advanced_amount','retention_amount','taxes_id','currency_id','date'], 25),
                                                              'kderp.supplier.payment.pay': (_get_order_from_supplier_payment_pay, None, 30),
                                                             })
              }    
purchase_order()