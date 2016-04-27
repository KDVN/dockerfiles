# -*- coding: utf-8 -*-
import re
import time

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_round, float_is_zero, float_compare
from openerp.tools.translate import _

class account_tax(osv.osv):
    _name = "account.tax"
    _description = "Account Tax"
    _inherit = "account.tax"
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            if record.type=='fixed':
                full_name = '{:20,.2f}'.format(record.amount)
            else:
                full_name = record.name
            res.append((record.id, full_name))
        return res
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context={}, count=False):
        if context.get('res_models',[]) and context.get('res_ids',[-1]):
            res_models=context.get('res_models',[])
            res_ids=[x if x else 0 for x in context.get('res_ids',[-1])]
            if len(res_models)==1:
                res_models.append(' ')
            if len(res_ids)==1:
                res_ids.append(-1)
            cr.execute("""Select 
                                id 
                        from
                             account_tax 
                        where coalesce(res_model,'')='' or (coalesce(res_model,'') in %s and coalesce(res_id,0) in %s)""" % (tuple(res_models),tuple(res_ids)))
            tax_ids=[]
            for tax_id in cr.fetchall():
                tax_ids.append(tax_id[0])
            args+=[('id','in',tax_ids)]
        return super(account_tax, self).search(cr, uid, args, offset, limit, order, context, count)
    
    def _get_default_value(self, cr, uid, context=None, field=''):
        if not context:
            context={}
        tax_type=context.get('type','received')
        default_list={}
        name=context.get('res_name','')
        value_amount=0
        if context.get('default_name',''):
            context['default_value']=context.pop('default_name')
        if context.get('default_value','').isdigit():
            value_amount=float(context.get('default_value','0'))

        if tax_type=='received':            
            default_list={
                'amount':value_amount,
                'account_collected_id':23, #Tax 133100 23 (Co the sua thanh thue nhap khau)
                'account_paid_id':23, #Tax 133100 23 (Co the sua thanh thue nhap khau)
                'base_code_id': 20, #Tax Base Amount
                'ref_base_code_id': 20,  #Tax Base Amount Refund
                'tax_code_id': 21, # Other Deducted Amount
                'ref_tax_code_id': 21, # Other Deducted Amount Refund
                'type':'fixed',
                'type_tax_use':'purchase',
                'applicable_type':True,
                'res_id':context.get('res_ids',[])[0] if context.get('res_ids',[]) else False,
                'res_model':context.get('res_models',[])[0] if context.get('res_models',[]) else '',
                'name':'VAT for '+ (name if name else '')}
        else:
            default_list={
                'amount':value_amount,
                'account_collected_id':95, #Tax "333110" 95 (Co the sua thanh thue nhap khau)
                'account_paid_id':95, #Tax "333110" 95 (Co the sua thanh thue nhap khau)
                'base_code_id': 22, #Tax Base Amount
                'ref_base_code_id': 22,  #Tax Base Amount Refund
                'tax_code_id': 23, # Other Issued Amount
                'ref_tax_code_id': 23, # Other Issued Amount Refund
                'type':'fixed',
                'type_tax_use':'sale',
                'applicable_type':True,
                'res_id':context.get('res_id',[])[0],
                'res_model':context.get('res_model',[])[0],
                'name':'For '+ (name if name else '')}
        return default_list['%s' % field]
    
    _columns={
              'default_tax':fields.boolean('Default'),
              'res_model':fields.char('Model',size=128),
              'res_id':fields.integer("Res ID"),
              }
    _defaults={
                'account_collected_id': lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='account_collected_id'),
                'account_paid_id':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='account_paid_id'),
                'base_code_id':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='base_code_id'),
                'ref_base_code_id':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='ref_base_code_id'),
                'tax_code_id':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='tax_code_id'),
                'ref_tax_code_id':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='ref_tax_code_id'),
                'type':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='type'),
                'type_tax_use':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='type_tax_use'),
                'amount':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='amount'),
                'res_id':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='res_id'),
                'res_model':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='res_model'),
                'name':lambda self, cr, uid, context: self._get_default_value(cr, uid, context,field='name'),
               }
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id,type_tax_use)', 'Tax Name must be unique per company!')
    ]
    
    def create(self, cr, uid, vals, context={}):
        new_acc_tax = super(account_tax, self).create(cr, uid, vals, context=context)
        return new_acc_tax
    
    def name_create(self, cr, uid, name, context={}):
        value_amount=0
        if not context:
            context={}
        context['default_name']=name

        rec_id = self.create(cr, uid,{}, context=context)
        return self.name_get(cr, uid, [rec_id], context)[0]
    
account_tax()

class account_move(osv.osv):
    _name='account.move'
    _inherit='account.move'
    
    _columns={
              'ref': fields.char('Reference', size=256),
              }
account_move()

class account_move_line(osv.osv):
    _name='account.move.line'
    _inherit='account.move.line'
    
    _columns={
              'ref': fields.related('move_id', 'ref', string='Reference', type='char', size=256, store=True),
              }
account_move_line()