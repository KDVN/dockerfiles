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

class incoterm(osv.osv):
    _name='incoterm'
    _description='Incoterm'
    
    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['code', 'name'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['code'] and name:
                name = record['code'] + ' - ' + name
            res.append((record['id'], name))
        return res
    
    _columns={
         'code':fields.char('Code',size=3,required=True),
         'name':fields.char('Name',size=64,required=True),
         'description':fields.char('Description',size=256),
            }
incoterm()