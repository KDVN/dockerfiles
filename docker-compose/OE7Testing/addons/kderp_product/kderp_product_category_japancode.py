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

from osv import fields,osv
from osv.orm import except_orm
import tools

class kderp_product_category_japan(osv.osv):
    _name = "kderp.product.category.japan"
    _description = "KDERP Product Category Follow Japan"
        
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        res = []
        reads = self.read(cr, uid, ids, ['name','code'], context)
        for record in reads:
            name=''
            if record:
                name = record['code']+" - "+record['name']
            res.append((record['id'], name))        
        return res
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, user, [('code','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids += self.search(cr, user, [('code','ilike',name)]+ args, limit=limit, context=context)
            ids += self.search(cr, user, [('name','ilike',name)]+ args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)
    
    _columns = {
       'code':fields.char('Code',size=4,required=True),
       'name':fields.char('Name',size=255,required=True)
    }
kderp_product_category_japan()

class product_product(osv.osv):
    _name = "product.product"
    _description = "Product"
    _inherit="product.product"
    
    _columns={
              'category_follow_japan_id':fields.many2one('kderp.product.category.japan','Kinden Corp. Category')
              }
product_product()
  