from openerp.osv import osv

from openerp import SUPERUSER_ID

class account_analytic_account(osv.osv):
    """Inherit Analytic Object (Job)"""
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'

    #Temporary
    def create1(self, cr, uid, vals, context=None):
        new_job_id=super(account_analytic_account, self).create(cr, uid, vals, context=context)
        #Create Stock Related Project
        try:
            context = context or {}
            ctx = context.copy()
            ctx['jobCode'] = vals['code']
            ctx['warehouseType'] = 'internal'
            sl_obj = self.pool.get('stock.location')
            stock_vals = {'name': vals.get('name'),
                          'account_analytic_id': new_job_id,
                          'usage':'internal'
                          }
            sl_obj.create(cr, SUPERUSER_ID, stock_vals, ctx)
            stock_vals['usage']= 'customer'
            ctx['warehouseType'] = 'customer'
            sl_obj.create(cr, SUPERUSER_ID, stock_vals, ctx)
        except:
            pass
        return new_job_id

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}

        if context.get('filter_job_stock', False):
            strSQL = """Select distinct aaa.id from account_analytic_account aaa left join stock_location sl on aaa.id = sl.account_analytic_id where coalesce(sl.id,0)=0 and aaa.state not in ('cancel','closed')"""
            cr.execute(strSQL)
            user_ids = [ruids[0] for ruids in cr.fetchall()]
            args.append((('id', 'in', user_ids)))
        return super(account_analytic_account, self).search(cr, user, args, offset=0, limit=None, order=None, context=None,
                                             count=False)