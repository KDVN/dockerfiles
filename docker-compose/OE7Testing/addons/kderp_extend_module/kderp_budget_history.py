from osv import osv, fields

class kderp_budget_history(osv.osv):
    _name='kderp.budget.history'
    _inherit='kderp.budget.history'
    _description="KDERP Budget History"
    
    def _get_total_history(self, cr, uid, ids, name, arg, context=None):
        res={}
        for kbh in self.browse(cr, uid, ids):
            res[kbh.id]=kbh.material + kbh.sub_contractor  + kbh.site_expense + kbh.kinden_salary_admin_cost + kbh.bussiness_profit
        return res
    
    _columns={
                      
         'amount':fields.function(_get_total_history,type='float',string='Total',method=True,
                                  store={
                                         'kderp.budget.history':(lambda self, cr, uid, ids, c={}: ids, None,25)})
         }
    
kderp_budget_history()