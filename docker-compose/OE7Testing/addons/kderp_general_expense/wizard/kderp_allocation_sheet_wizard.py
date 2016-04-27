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
from datetime import date
from kderp_base.kderp_base import diff_month

class kderp_create_allocation_sheet(osv.osv_memory):
    _name = 'kderp.create.allocation.sheet'
    _description = 'KDERP Wizard Create allocation Sheet'
    
    ALLOCATION_MONTH = [(1,'1 Month'),
                        (2,'For End of this year'),
                        (-1,'Custom')]
    
    def _get_budget_default(self, cr, uid, context = {}):
        budget = self.pool.get('account.budget.post').search(cr, uid, [('code','ilike','A31')])
        return budget[0] if budget else False
    
    def _get_default_value(self, cr, uid, context = {}, field='number_of_month'):
        if not context:
            context = {}
        ge_id = context.get('ge_id', False)
        if ge_id:
            ge_pool = self.pool.get('kderp.other.expense')
            ge = ge_pool.read(cr, uid, ge_id, [field])
            return ge[field] if ge else False  
        else:
            return False    
    
    _columns = {
                'allocating_begin_date':fields.date('Start Date',required=True),
                'startdate_default':fields.boolean('Start Date Defaults',invisible=True),
                'number_of_month':fields.integer("Allocated Months", help='Number of months expense will be allocated automatically. This field use for automatically create Allocation Sheet'),                
                'allocated_selection':fields.selection(ALLOCATION_MONTH,'Number of Months', required = True),
                'allocated_to_month':fields.integer(""),
                'section_id':fields.many2one('hr.department','Allocated to Section'),
                'budget_id':fields.many2one('account.budget.post','Budget', required = True),
                }
    _defaults={
               'allocated_selection':lambda *x:1,
               'number_of_month': _get_default_value,
               'allocating_begin_date':lambda self, cr, uid, context: self._get_default_value(cr, uid, context, 'allocating_begin_date'),
               'startdate_default': lambda self, cr, uid, context: True if self._get_default_value(cr, uid, context, 'allocating_begin_date') else False,
               'budget_id':_get_budget_default
               }
    
    def create_allocation_sheet(self, cr, uid, ids, context={}):
        """
        Create Allocation Sheet for Prepaid and Asset
        """
        if not context:
            context = []
        obj = self.browse(cr,  uid, ids[0], context)
        ge_obj = self.pool.get('kderp.other.expense')
        ge_id = context.get('ge_id', False)
        
        if ge_id:
            if not obj.startdate_default:
                val = {'number_of_month': obj.number_of_month}
                
                ge_obj.write(cr, uid, [ge_id], val)
            ge = ge_obj.browse(cr, uid, ge_id)            
            
            number_of_month = obj.number_of_month #Tong so nam can chi chi phi
            current_allocated = ge.allocating_date #Da chi chi phi den ngay (ca trang thai draft)
            allocating_begin_date = obj.allocating_begin_date #Ngay bat dau chi chi phi
            from datetime import datetime
            if allocating_begin_date:                             
                allocating_begin_date = datetime.strptime(allocating_begin_date, "%Y-%m-%d").date()
            allocated = True
            month_allocated = 0
           
            #So thang can tao Allocation
            if obj.allocated_selection == -1:
                month = obj.allocated_to_month
            elif obj.allocated_selection == 2:
                need_allocated = 1
                if current_allocated:
                    tmp_currrent_allocated = datetime.strptime(current_allocated, "%Y-%m-%d").date()
                    need_allocated = diff_month(tmp_currrent_allocated, date.today()) #Need allocate today
                month_current_endofyear =  diff_month(allocating_begin_date, date(date.today().year, 12, 31))
                month = need_allocated + month_current_endofyear                
            else:
                month =1
            
            if allocating_begin_date:
                if not current_allocated:
                    allocated = False
                    current_allocated = allocating_begin_date 
                else:
                    current_allocated = datetime.strptime(current_allocated, "%Y-%m-%d").date()                
                month_allocated = diff_month(allocating_begin_date, current_allocated) + 1 if allocated else 0

            if month_allocated < number_of_month:
                from dateutil.relativedelta import relativedelta
                month_create = month if (month_allocated + month) <= number_of_month else number_of_month - month_allocated
                exp = {}
                new_related_ids = []
                exp_date = (current_allocated + relativedelta(months=-1)) if not allocated else current_allocated 
                for m in range(1, month_create + 1):
                    exp['expense_type'] = 'monthly_expense'
                    exp['partner_id'] = 1
                    exp['address_id'] = 1                    
                    exp['date'] = exp_date +  relativedelta(months=m)
                    exp['taxes_id'] = [(6, False, False)],
                    exp['description'] = 'Allocated Expense %s%s' % (exp['date'].strftime("%b.%Y"), "\n" + ge.description if ge.description else "") 
                    context['general_expense'] = True
                    date_string = exp['date'].strftime("%Y-%m-%d")                    
                    job_ids = self.pool.get('account.analytic.account').search(cr, uid, [('date_start','<=',date_string),('date','>=',date_string),('general_expense','=',True)])                    
                    
                    if job_ids:
                        job_id = job_ids[-1]
                    else:
                        continue
                    exp['name'] = ge_obj.new_code(cr, uid, 0, job_id, 'E','')['value']['name']
                    exp['account_analytic_id'] = job_id
                    exp_line = []
                    for gel in ge.expense_line:
                        if m + month_allocated < number_of_month:
                            allocated_amount = round(gel.amount / number_of_month)
                        else:
                            allocated_amount = gel.amount - round(gel.amount / number_of_month) * (number_of_month - 1)
                        exp_line.append((0, False, 
                                         {'account_analytic_id': job_id,
                                          'budget_id': obj.budget_id.id,
                                          'belong_expense_id': ge.id,
                                          'asset_id': ge.link_asset_id.id if ge.link_asset_id else False,
                                          'amount': allocated_amount,
                                          'section_id': obj.section_id.id if obj.section_id else False
                                        }))
                    exp['expense_line'] = exp_line
                    new_related_ids.append(ge_obj.create(cr, uid, exp, context))
                #ge_obj.write(cr, uid, new_related_ids, {'taxes_id': False})
        return True

kderp_create_allocation_sheet()