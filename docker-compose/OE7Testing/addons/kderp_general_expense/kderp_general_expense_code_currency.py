from openerp.osv import fields, osv


class kderp_general_expense_code_currency(osv.osv):
    _name='kderp.general.expense.code.currency'
    _description='KDERP General Expense Currency'
    _rec_name = 'name'
    
    _columns={
               'name':fields.many2one('res.currency','Cur.',required = True),
               'rate':fields.float('Ex.Rate',digits = (12,2),required = True),
               'general_expense_code_id':fields.many2one('kderp.general.expense.code','General Expense',required=True),
              }
    
kderp_general_expense_code_currency()