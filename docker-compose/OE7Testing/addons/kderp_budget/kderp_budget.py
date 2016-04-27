from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_budget_data(osv.osv):
    _name = 'kderp.budget.data'
    _description = 'Budget Data for Job (Kinden)'
    
    _order="account_analytic_id desc, budget_code asc"
    
    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        res=[]
        for record in self.browse(cr, uid, ids):
            name = "%s - %s" % (record.account_analytic_id.code, record.budget_id.code)  
            res.append((record['id'], name))
        return res
    
    _columns={
              'budget_id':fields.many2one("account.budget.post","Code",required=True,select=1),
              'budget_code': fields.related('budget_id', 'code', type="char",size=8,store=True,select=1),
              
              'planned_amount':fields.float("Amount",required=True, digits_compute=dp.get_precision('Budget')),
              'account_analytic_id':fields.many2one('account.analytic.account','Job',ondelete="restrict",select=1),
              }
    
    _sql_constraints = [
        ('unique_budget_analytic_account', 'unique (budget_id,account_analytic_id)',  'Budget and Job must be unique')]
    
    _defaults={
               'planned_amount': lambda *x: 0.0,
               }
        
kderp_budget_data()

class account_budget_post(osv.osv):
    _inherit='account.budget.post'
    _name='account.budget.post'
    _order ="code,name"
    _sql_constraints=[('kderp_budget_code','unique(code)','Code for Budget must be unique !')]
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        job_id = context.get('job_id',0)
        
        if context.has_key('job_id'):
            if not job_id:
                job_id=0          
            budget_ids = []
            cr.execute("""select 
                            budget_id
                        from 
                            kderp_budget_data
                        where 
                            account_analytic_id=%s""" % job_id)
            for budget_id in cr.fetchall():
                budget_ids.append(budget_id[0])
            args.append((('id', 'in', budget_ids)))

        return super(account_budget_post, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)    
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        
        if name:
            ids = self.search(cr, user, [('code', '=', name)]+args,  limit=limit,context=context)
            if ids:
                ids = self.search(cr, user, [('code',operator, name)]+args,limit=limit,context=context)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)]+ args,limit=limit,context=context)
        else:
            ids = self.search(cr, user, args,limit=limit,context=context)
        return self.name_get(cr, user, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = (record['code'] + ' - ' + record['name']) if record['code'] else record['name']  
                
            res.append((record['id'], name))
        return res
account_budget_post()


class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    
    _columns={    
              'kderp_budget_data_line': fields.one2many('kderp.budget.data', 'account_analytic_id', 'Detail of Budget'),
              }
account_analytic_account()