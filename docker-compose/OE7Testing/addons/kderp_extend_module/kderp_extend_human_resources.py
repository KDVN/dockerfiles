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
from openerp.tools.translate import _
from openerp import tools


class hr_department(osv.osv):
    _name = "hr.department"
    _inherit = "hr.department"

    def _dept_name_get_fnc(self, cr, uid, ids, name=None, args=None, context=None):
        if context == None:
            context = {}
        res = {}
        for hr in self.browse(cr, uid, ids, context=context):
            res[hr.id] = "%s - %s" % (hr.code,hr.name)
        return res
    
    _rec_name='complete_name' 
    _columns={
              'complete_name':fields.function(_dept_name_get_fnc,type='char',size=64,method=True, string='Name',
                                            store={
                                                   'hr.department': (lambda self, cr, uid, ids, c={}: ids, ['code','name'], 5),
                                                   })
              
              }
  
         
hr_department()
