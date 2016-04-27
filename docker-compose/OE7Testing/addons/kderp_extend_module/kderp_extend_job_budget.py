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

import time
import openerp.addons.decimal_precision as dp

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc


class kderp_budget_data(osv.osv):
    _name = 'kderp.budget.data'
    _inherit = 'kderp.budget.data'
                
    _description = 'Budget Data for Job (Kinden)'
        
    def _get_summaryofbudget(self, cr, uid, ids, name, args, context):
        res = {}
        if ids:
            budget_data_ids = ",".join(map(str,ids))
            cr.execute("""Select 
                            kbd.id,
                            planned_amount,
                            sum(coalesce(amount,0)) as expense_amount                      
                        from 
                            kderp_budget_data kbd 
                        left join 
                            kderp_expense_budget_line kebl on kbd.account_analytic_id=kebl.account_analytic_id and kbd.budget_id = kebl.budget_id
                        where
                            kbd.id in (%s)
                        group by
                            kbd.id""" % budget_data_ids)
                        
            for id, pl_amount, amount in cr.fetchall():
                res[id]={
                         'balance_amt': pl_amount-amount
                         }
        return res
    
    def _get_budget_line_from_job_budget_line(self, cr, uid, ids, context=None):
        res=[]
        for kebl in self.pool.get('kderp.expense.budget.line').browse(cr,uid,ids):
            for kbd in kebl.account_analytic_id.kderp_budget_data_line:
                if kbd.budget_id.id==kebl.budget_id.id:
                    res.append(kbd.id)
        return list(set(res))
    
    _columns={
              'balance_amt':fields.function(_get_summaryofbudget,string='Balance',digits_compute=dp.get_precision('Budget'),method=True,type='float',size=8,multi='sums',
                                            store={
                                                     'kderp.budget.data':(lambda self, cr, uid, ids, c={}: ids,None,50),
                                                     'kderp.expense.budget.line':(_get_budget_line_from_job_budget_line,None,50),
                                                      }
                                            )
                                               
              }
    _defaults={
               'balance_amt': lambda *x: 0.0,
               }
kderp_budget_data()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

