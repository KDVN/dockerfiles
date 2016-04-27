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

from osv import fields, osv

class kderp_control_area(osv.osv):
    """KDERP Contral Area Model"""
    _name = 'kderp.control.area'

    def name_get(self, cr, uid, ids, context=None):
        context = context or {}
        result = []
        for var in self.browse(cr, uid, ids, context=context):
            if context.get('code_only', False):
                res = (var.id, var.code)
            elif context.get('name_only', False):
                res = (var.id, var.name)
            else:
                res = (var.id, "%s - %s" % (var.code,var.name))
            result.append(res)
        return result

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}

        if name:
            name=name.strip()
            kca_ids = self.search(cr, uid, [('code', '=', name)] + args, limit=limit, context=context)
            if not kca_ids:
                kca_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not kca_ids:
                kca_ids = self.search(cr, uid, [('name', '=', name)] + args, limit=limit, context=context)
            if not kca_ids:
                kca_ids = self.search(cr, uid,[('name', 'ilike', name)] + args, limit=limit, context=context)
        else:
            kca_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, kca_ids, context=context)

    _columns = {
        'code':fields.char('Code', size=4, required=True),
        'name':fields.char('Name', size=128, translate=True, required = True),

        # 'control_job_ids':fields.one2many('account.analytic.account','control_area_id','Control Job(s)'),
        # 'support_job_ids': fields.one2many('account.analytic.account', 'support_area_id', 'Support Job(s)'),
    }

    _sql_constraints=[('kderp_control_area_unique_code',"unique(code)",'Code must be unique!'),
                      ("kderp_control_area_code_template","check(code ~ 'CA[0-9][0-9]')","Code like CA##")]
kderp_control_area()