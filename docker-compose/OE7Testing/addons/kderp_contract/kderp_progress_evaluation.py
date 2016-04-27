from openerp.osv.orm import Model
from openerp.osv import fields
import openerp.addons.decimal_precision as dp
import re

class kderp_progress_evaluation(Model):
    _name='kderp.progress.evaluation'
    _description='KDERP Progress Evaluation Sheet'
    
    def _get_new_seq(self, cr, uid, context={}):
        from kderp_base import kderp_base
        if not context:
            context={}
        new_val = kderp_base.get_new_from_tree(cr, uid, context.get('id',False), self,context.get('progress_lines',[]),'name', 0, 1, context)
        return new_val
    
    _columns={
            'contract_id':fields.many2one('kderp.contract.client','Contract',required=True),
            'name':fields.integer('No.',required=True),
            'currency_id':fields.many2one('res.currency','Cur.',required=True),
            'date':fields.date('Date'),
            'advanced':fields.float('Advanced'),
            'retention':fields.float('Retention'),
            'amount':fields.float('Amount'),
            'vat':fields.float('VAT'),
             }
    _sql_constraints = [
        ('client_payment_unique_no', 'unique(contract_id,name,currency_id)', 'Number of progress and Currency must be unique !')
        ]
    _defaults={
               'name':_get_new_seq
               }
kderp_progress_evaluation()
