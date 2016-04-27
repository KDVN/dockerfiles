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

from openerp.osv import fields, osv, orm

class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    PO_TYPE = (('m','Material'),('s','Sub-Contractor'),('ms','Material & Sub-Contractor'),('i','Using for Internal Only'))

    _columns = {
        'typeoforder': fields.selection(PO_TYPE,
                                                'Type of order',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},required=True),
    }

class purchase_order_line(osv.osv):
    """
        Add new field link Prepaid Order to Purchase Order Line
    """
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'
    
    _columns = {
                'stock_move_id':fields.many2one('stock.move','Stock Move ID',help='Using for moving expense')
                }