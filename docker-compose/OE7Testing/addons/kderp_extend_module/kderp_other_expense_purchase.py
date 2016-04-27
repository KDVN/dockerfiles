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

class purchase_order_line(osv.osv):
    _name='purchase.order.line'
    _inherit='purchase.order.line'
    
    def _check_job_budget(self, cr, uid, ids, context=None):
        job_budget_list=[]
        for kel in self.browse(cr, uid, ids):
            job_id=kel.account_analytic_id.id
            budget_id=kel.product_id.budget_id.id if kel.product_id.budget_id else 0 
            job_budget_list.append((job_id,budget_id))
        job_budget_list=",".join(map(str,job_budget_list))
        cr.execute("""Select id from kderp_budget_data where (account_analytic_id,budget_id) in (%s)""" % job_budget_list)
        if cr.rowcount:
            return True
        else:
            return False
    
    _constraints = [(_check_job_budget, 'Please check you Job and Budget you have just modify (No Budget Job) !', ['account_analytic_id','budget_id'])]
    
purchase_order_line()

class kderp_other_expense_line(osv.osv):
    _name='kderp.other.expense.line'    
    _inherit='kderp.other.expense.line'
        
    def _get_budget_remain(self, cr, uid, ids, fields, arg, context={}):
        pol_ids=",".join(map(str,ids))
        res={}
        cr.execute("""Select
                        koel.id,
                        planned_amount-sum(coalesce(kebl.amount,0))
                    from    
                        kderp_other_expense_line koel
                    left join
                        kderp_other_expense koe on expense_id = koe.id
                    left join
                        kderp_budget_data kbd on koel.budget_id=kbd.budget_id and koel.account_analytic_id=kbd.account_analytic_id
                    left join
                        kderp_expense_budget_line kebl on koel.budget_id=kebl.budget_id and 
                                                          koel.account_analytic_id=kebl.account_analytic_id and 
                                                          (koe.date>kebl.date or (kebl.date=koe.date and koe.name>kebl.name))
                    where
                        koel.id in (%s)
                    Group by
                        koel.id,kbd.id""" % (pol_ids))

        for koel_id,remaining in cr.fetchall():
            res[koel_id]=remaining
        return res
    
    _columns={
              'remaining_amount':fields.function(_get_budget_remain,digits_compute=dp.get_precision('Amount'),string='Remaining Amount',
                                                type='float',method=True),
              }
    
    def _check_job_budget(self, cr, uid, ids, context=None):
        job_budget_list=[]
        for kel in self.browse(cr, uid, ids):
            job_id=kel.account_analytic_id.id
            budget_id=kel.budget_id.id
            job_budget_list.append((job_id,budget_id))
        job_budget_list=",".join(map(str,job_budget_list))
        cr.execute("""Select id from kderp_budget_data where (account_analytic_id,budget_id) in (%s)""" % job_budget_list)
        if cr.rowcount:
            return True
        else:
            return False
        
    _constraints = [(_check_job_budget, 'Please check you Job and Budget you have just modify (No Budget Job) !', ['account_analytic_id','budget_id'])]

kderp_other_expense_line()