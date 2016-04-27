import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_expense_budget_line(osv.osv):
    _name='kderp.expense.budget.line'
    _inherit='kderp.expense.budget.line'
    _description='Expense Budget Line'
    
    def _get_withoutcontract(self, cr, uid, ids, name, args,context={}):
        res={}
        
        dict_obj={'purchase.order':True}
        kbudget_obj=self.pool.get('kderp.budget.data')
        
        for kebl in self.browse(cr, uid, ids, context):
            if kebl.expense_obj in dict_obj:
                res[kebl.id]=self.pool.get(kebl.expense_obj).browse(cr, uid, kebl.expense_id).without_contract
            else:
                res[kebl.id]=True
            kbd_ids=kbudget_obj.search(cr, uid, [('budget_id','=',kebl.budget_id.id),('account_analytic_id','=',kebl.account_analytic_id.id)])
            if kbd_ids:
                kbudget_obj.write(cr, uid, kbd_ids,{})
        return res
    
    def _get_curr_period_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        list_cal = []
        kebl_ids=",".join(map(str,ids))
        cr.execute("""Select
                        kebl.id,
                        pp.currency_id,
                        po.period_id as period_id,
                        date_order as date,
                        po.partner_id as partner_id,
                        notes as description,
                        po.name as name
                    from
                        kderp_expense_budget_line kebl
                    left join
                        purchase_order po on kebl.expense_id=po.id and kebl.expense_obj='purchase.order'
                    left join
                        product_pricelist pp on pricelist_id=pp.id
                    where kebl.expense_obj='purchase.order' and kebl.id in (%s)
                    Union
                    Select
                        kebl.id,
                        koe.currency_id,
                        koe.period_id as period_id,
                        koe.date,
                        koe.partner_id,
                        koe.description,
                        koe.name
                    from
                        kderp_expense_budget_line kebl
                    left join
                        kderp_other_expense koe on kebl.expense_id=koe.id and kebl.expense_obj='kderp.other.expense'
                    where kebl.expense_obj='kderp.other.expense' and kebl.id in (%s)""" % (kebl_ids,kebl_ids))
        kebl_ids_update=[]
        for id,currency_id,period_id,date,partner_id,description,name in cr.fetchall():
                if name:
                    if 'currency_id' in name:
                        kebl_ids_update.append(id)
                res[id]={'exrate':1} #Exrate temporary
                res[id].update({'currency_id':currency_id})
                res[id].update({'period_id':period_id if period_id else False})
                res[id].update({'name':name})
                res[id].update({'partner_id':partner_id})
                res[id].update({'date':date})
                res[id].update({'description':description})
        if kebl_ids_update:
            self.write(cr, uid, kebl_ids_update,{})
        return res
    
    
    def _get_curr_period_date1(self, cr, uid, ids, name, args, context=None):
        res = {}
        list_cal = []
        for kebl in self.browse(cr,uid,ids):
            list_cal.append([kebl.id,str(kebl.expense_obj),[kebl.expense_id]])
            res[kebl.id]={'exrate':False,
                     'currency_id':False,
                     'period_id':False,
                     'date':False,
                     'partner_id':False,
                     'description':False,
                     'name':False}

        for lst in list_cal:
            for obj in self.pool.get(lst[1]).browse(cr, uid,lst[2]):
                res[lst[0]]['exrate']=obj.exrate
                res[lst[0]]['currency_id']=obj.currency_id.id
                res[lst[0]]['period_id']=obj.period_id.id if obj.period_id else False
                res[lst[0]]['exrate']=obj.exrate
                res[lst[0]]['name']=obj.name
                res[lst[0]]['partner_id']=obj.partner_id.id
                if lst[1]=='purchase.order':
                    res[lst[0]]['date']=obj.date_order
                    res[lst[0]]['description']=obj.notes
                else:
                    res[lst[0]]['description']=obj.description                
                    res[lst[0]]['date']=obj.date
        return res
    
    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = []
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for pol in po.order_line:
                if pol.expense_budget_line:
                    result.append(pol.expense_budget_line.id)
        return list(set(result))
    
    def _get_other_expense(self, cr, uid, ids, context=None):
        result = []
        for koe in self.pool.get('kderp.other.expense').browse(cr, uid, ids, context=context):
            for koel in koe.expense_line:
                if koel.expense_budget_line:
                    result.append(koel.expense_budget_line.id)
        return list(set(result))
    
    _columns={              
           
              'without_contract':fields.function(_get_withoutcontract,type='boolean',method=True,string='Without Contract',
                                  store = {
                                            'purchase.order': (_get_purchase_order, ['without_contract'], 40),
                                            'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                          }),
              'exrate':fields.function(_get_curr_period_date, string='Exrate', type='float', multi='kderp_get_id', digits_compute=dp.get_precision('Account'),
                                store = {
                                    'purchase.order':(_get_purchase_order, ['currency_id','pricelist_id','date_order'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['currency_id','date'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'partner_id':fields.function(_get_curr_period_date,string='Supplier', type='many2one', relation='res.partner',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['partner_id'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['partner_id'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              
              'name':fields.function(_get_curr_period_date,string='Name', type='char',size=64, multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['name'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['name'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'description':fields.function(_get_curr_period_date,string='Desc.', type='char',size=256,multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['notes'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['description'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
                            
              'currency_id':fields.function(_get_curr_period_date,string='Curr.', type='many2one', relation='res.currency',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['currency_id','pricelist_id'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['currency_id'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'period_id':fields.function(_get_curr_period_date, string='Period', type='many2one', relation='account.period',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['period_id'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['period_id'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              'date': fields.function(_get_curr_period_date ,string='Date of Order', type='date',multi='kderp_get_id',
                                store = {
                                    'purchase.order': (_get_purchase_order, ['date_order'], 20),
                                    'kderp.other.expense':(_get_other_expense, ['date'], 20),
                                    'kderp.expense.budget.line': (lambda self, cr, uid, ids, c={}: ids,None, 15),
                                }),
              }
 
kderp_expense_budget_line()
