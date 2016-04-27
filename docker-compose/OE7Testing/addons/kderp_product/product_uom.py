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

from osv import osv, fields
import pooler

from tools import config
from tools.translate import _


#----------------------------------------------------------
# UOM
#----------------------------------------------------------

class product_uom(osv.osv):
    _name = 'product.uom'
    _inherit='product.uom'
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids += self.search(cr, user, [('name','ilike',name)]+ args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
product_uom()