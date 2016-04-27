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

#
# Inherit of Sequence change code default stock picking
#
class ir_sequence(osv.osv):
    _inherit = "ir.sequence"

    def get(self, cr, uid, seqCode, context={}):
        """
            Check if get new code for Stock Picking will apply custom code in Kinden
        """

        obj_check = 'stock.picking'
        if seqCode.find(obj_check)>=0:
            posFind = seqCode.rfind('.') if seqCode.rfind('.') else seqCode.rfind('_')
            return self.pool.get(obj_check).get_newcode(cr, uid, seqCode[posFind+1:])
        else:
            return super(ir_sequence, self).get(cr, uid, seqCode, context)