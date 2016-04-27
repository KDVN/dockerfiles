from openerp.osv.orm import Model
from openerp.osv import fields, osv

class account_analytic_account(Model):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if 'filter_by_location' in context:
            location_id  = context.get('filter_by_location', False)
            arg = [('id','=',0)]
            if location_id:
                wh_obj =  self.pool.get('stock.location').browse(cr, user, location_id)
                job_ids = [job.id for job in wh_obj.job_related_ids]
                arg = [('id','in', job_ids)]
            args += arg
        return super(account_analytic_account, self).search(cr, user, args, offset=offset, limit= limit, order=order, context=context, count=count)

    _columns={             
                'moving_expense_in_ids':fields.one2many('stock.move','to_analytic_id','Expense In',context={'expense_type': 'in'}, readonly=1),
                'moving_expense_out_ids':fields.one2many('stock.move','from_analytic_id','Expense Out',context={'expense_type': 'out'}, readonly=1),
    }

