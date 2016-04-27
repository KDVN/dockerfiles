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

#----------------------------------------------------------
# Categories
#----------------------------------------------------------
class kderp_budget_category(osv.osv):
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context):
        res = self.name_get(cr, uid, ids, context)
        return dict(res)

    _name = "kderp.budget.category"
    _description = "KDERP Budget Category"
    _columns = {
        'name':fields.char('Name', size=64, required=True),
        'cat_code':fields.char('Code', size=64),
        'complete_name': fields.function(_name_get_fnc, method=True, type="char", string='Name'),
        'parent_id': fields.many2one('kderp.budget.category','Parent Category', select=True),
        'child_id': fields.one2many('kderp.budget.category', 'parent_id', string='Child Categories'),
        'sequence': fields.integer('Sequence'),
        'budget_post_id':fields.one2many('account.budget.post','budget_categ_id',string='Products'),
        'type':fields.selection([('expense','Expense'),('supervisor','Supervisor'),('commission','Commission'),('admin','Administration Cost'),('profit','Profit')],'Type',)
    }
    _order = "sequence"
    def _check_recursion(self, cr, uid, ids):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from kderp_budget_category where id in ('+','.join(map(str,ids))+')')
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
    ]
    def child_get(self, cr, uid, ids):
        return [ids]

kderp_budget_category()

#----------------------------------------------------------
# account_budget_post
#----------------------------------------------------------
class account_budget_post(osv.osv):
    _name = 'account.budget.post'
    _description = 'Budgetary Position'
    _inherit='account.budget.post'
    _columns = {
        'budget_categ_id': fields.many2one('kderp.budget.category','Category', required=True, change_default=True),
    }
    def _default_category(self, cr, uid, context={}):
        if context:
            if context.get('budget_categ_id',False):
                return context['budget_categ_id']
        return False

    _defaults = {
        'budget_categ_id' : _default_category,
    }
account_budget_post()

