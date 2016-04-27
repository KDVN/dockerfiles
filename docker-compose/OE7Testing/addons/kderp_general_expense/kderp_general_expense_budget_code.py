from openerp.osv import fields, osv
import re
from openerp.osv import fields
import openerp.addons.decimal_precision as dp

class kderp_general_expense_budget_code(osv.osv):
    _name='kderp.general.expense.budget.code'
    _rec_name = 'code'
    _order='code'
    _description='KDERP General Expense Budget Code'
 
    _columns={
               'code':fields.char('Code',size=8,required=True,select=1),
               'name':fields.char('Name',size=128,select=1,required=True),
               'parent_id':fields.many2one('kderp.general.expense.budget.code','Parent Code', select=True, ondelete='restrict'),
               'sub_budget_ids': fields.one2many('kderp.general.expense.budget.code', 'parent_id', 'Sub Budget'),
               'budget_line_ids':fields.one2many('kderp.general.expense.code.budget.data','budget_id','Budget Detail' ,ondelete='restrict',readonly=True),
               'no_filter':fields.boolean('No Filter')
            }
    
    _sql_constraints = [('general_expense__budget_code_unique',"unique(code)","KDERP Error: The General Expense Budget Code and type must be unique !")]
   
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        gec_id = context.get('gec_id',0)
        if context.has_key('gec_id'):
            if not gec_id:
                gec_id=0          
            budget_ids = []
            cr.execute("""select 
                                id 
                            from 
                                kderp_general_expense_budget_code 
                            where 
                                no_filter=True
                            union 
                            select
                                budget_id
                            from
                                kderp_general_expense_code_budget_data kgecbd
                            where
                                general_expense_code_id=%s
                            union
                            select
                                kgebc.id
                            from
                                kderp_general_expense_code_budget_data kgecbd
                            left join
                                kderp_general_expense_budget_code kgebc on kgecbd.budget_id=parent_id
                            where
                                general_expense_code_id=%s""" % (gec_id,gec_id))
            for budget_id in cr.fetchall():
                budget_ids.append(budget_id[0])
            args.append((('id', 'in', budget_ids)))
        return super(kderp_general_expense_budget_code, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}
        if name:
            name=name.strip()
            ctc_ids = self.search(cr, uid, [('code', '=', name)] + args, limit=limit, context=context)
            if not ctc_ids:
                ctc_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not ctc_ids:
                ctc_ids = self.search(cr, uid,[('name', 'ilike', name)] + args, limit=limit, context=context)
        else:
            ctc_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ctc_ids, context=context)   
   
    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = (record['code'] + ' - ' + record['name']) if record['code'] else record['name']  
                
            res.append((record['id'], name))
        return res 
    
kderp_general_expense_budget_code()

