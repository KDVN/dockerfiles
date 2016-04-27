from openerp.osv import fields, osv
import time
from datetime import datetime

class kderp_other_expense_line(osv.osv):
    _name='kderp.other.expense.line'
    _inherit='kderp.other.expense.line'
    _description='KDERP Other Expense Line'
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            if not ids:
                ids = self.search(cr, user, [('account_analytic_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('budget_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name','ilike',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('asset_id','ilike',name)]+ args, limit=limit, context=context)
            if not ids:
                check=name.replace(',','')
                if check.isdigit():
                    ids = self.search(cr, user, [('amount','=',name)]+ args, limit=limit, context=context)            
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    _columns={
                'asset_id':fields.many2one('kderp.asset.management','Asset Code',ondelete="restrict",),
              }
kderp_other_expense_line()

class kderp_asset_management(osv.osv):
    _name = 'kderp.asset.management'
    _inherit='kderp.asset.management'
    _description='KDERP Asset Management'
    
    def _get_depreciation_amount(self, cr, uid, ids, name, args, context={}):
        res={}
        if not context:
            context={}
        if ids:
            kap_ids=",".join(map(str,ids))
            for id in ids:
                res[id]={'current_accumulated_amount':0.0,
                         'current_remaining':0.0}
                
            cr.execute("""Select 
                            kam.id as asset_id,
                            sum(coalesce(kad.amount,0))+(case when using_remaining then price*quantity -remaining_amount else 0 end) as current_accumulated_amount,
                            price*quantity-(sum(coalesce(kad.amount,0))+(case when using_remaining then price*quantity -remaining_amount else 0 end) ) as current_remaining
                        from
                            kderp_asset_management kam
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        left join
                            kderp_asset_depreciation kad on kam.id=asset_id
                        where
                            state not in ('draft','liquidated') and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and kam.id in (%s)
                        group by
                            kam.id""" % (kap_ids))
            for kap_obj in cr.dictfetchall():
                res[kap_obj.pop('asset_id')]=kap_obj
        return res
    
    def _get_check_fixed(self, cr, uid, ids, name, args, context={}):
        res={}
        if not context:
            context={}
        for kap in self.browse(cr, uid, ids, context):
            if kap.type_asset_acc_id.typeofasset_id.name=='FA' and len(kap.code)==len('HFA1-13-14-0001'):
                res[kap.id]=True
            else:
                res[kap.id]=False
        return res
#Method for Store
    def _get_asset_other_expense(self, cr, uid, ids, context=None):
        res=[]
        for kot in self.pool.get('kderp.other.expense').browse(cr, uid, ids):
            for kotl in kot.expense_line:
                if kotl.asset_id:
                    res.append(kotl.asset_id.id)
        return list(set(res))
    
    def _get_asset_other_expense_line(self, cr, uid, ids, context=None):
        res=[]
        for kotl in self.pool.get('kderp.other.expense.line').browse(cr, uid, ids, context):        
            if kotl.asset_id:
                res.append(kotl.asset_id.id)
        return list(set(res))    
    
    def _get_asset_general_acc_code(self, cr, uid, ids, context=None):
        res=[]
        if ids:
            kaca_ids=",".join(map(str,ids))
            cr.execute("""Select distinct kam.id from kderp_asset_management kam left join kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id where kaca.id in (%s)""" % (kaca_ids))
            for kam_id in cr.fetchall():
                res.append(kam_id[0])
        return res
    
    def _get_asset_general_type_of_asset(self, cr, uid, ids, context=None):
        res=[]
        if ids:
            kaca_ids=",".join(map(str,ids))
            cr.execute("""Select 
                                distinct kam.id 
                          from 
                              kderp_asset_management kam 
                          left join 
                              kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id 
                          left join
                              kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                          where ktoa.id in (%s)""" % (kaca_ids))
            for kam_id in cr.fetchall():
                res.append(kam_id[0])
        return res

    _columns={
               'asset_ids':fields.one2many('kderp.asset.depreciation','asset_id',readonly=True),#Link to Detail of Depreciation
               'partial_liquitation_ids':fields.one2many('kderp.asset.partial.liquidation','asset_id','Partial Liquidation',states={'liquidated':[('readonly',True)]}),#Link to Detail of Partial Liquidation
               
               'remaining_amount':fields.float('Remaining'), #Using for OLD Data import from accounting
               'using_remaining':fields.boolean('Using Remaining'),#Using for OLD Data import from accounting,
               #'depreciation_start_date':fields.date('Depreciation Start Date',help="If this date if not available, system will calculate based on date of invoice."),
               'current_accumulated_amount':fields.function(_get_depreciation_amount,type='float',method=True,string='Accumulated Amt.',multi="_get_dep_amt",
                                                            store={                                                                   
                                                                   'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['price','quantity','state'], 10),
                                                                   'kderp.other.expense':(_get_asset_other_expense,['state'],15),
                                                                   'kderp.other.expense.line':(_get_asset_other_expense_line,['amount','asset_id'],15),
                                                                   }),
               'current_remaining':fields.function(_get_depreciation_amount,type='float',method=True,string='Remaining Amt.',multi="_get_dep_amt",
                                                   store={                                                                   
                                                                   'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['price','quantity','state'], 10),
                                                                   'kderp.other.expense':(_get_asset_other_expense,['state'],15),
                                                                   'kderp.other.expense.line':(_get_asset_other_expense_line,['amount','asset_id'],15),
                                                                   }),
               'fixed_asset':fields.function(_get_check_fixed,method=True,type='boolean',string='Fixed Asset',store={                                                                   
                                                                   'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['type_asset_acc_id'], 10),                                                                   
                                                                   'kderp.asset.code.accounting':(_get_asset_general_acc_code,['typeofasset_id'],15),
                                                                   'kderp.type.of.asset':(_get_asset_general_type_of_asset,['name'],15),
                                                                   }),
                'expense_id':fields.many2one('kderp.other.expense', 'Expense', domain=[('expense_type','in',('expense','fixed_asset')),('link_asset_id','=',False)],
                                             context={'general_expense': True}, readonly=True, states={'draft':[('readonly',False)]})
              }
    def onchange_asset(self, cr, uid, ids, expense_id, desc, supplier, price, dateofinvoice):
        value = {}
        if expense_id:
            exp_obj = self.pool.get('kderp.other.expense')
            exp = exp_obj.browse(cr, uid, expense_id)
            if not desc:
                for var_expense in exp.expense_line:
                    value['name'] = var_expense.name
            if not supplier:
                value['supplier'] = exp.partner_id.name
            if not price:
                value['price'] = exp.amount_untaxed
            if not dateofinvoice:
                for var_payment in exp.supplier_payment_expense_ids:
                    for var_vat in var_payment.kderp_vat_invoice_ids:
                        value['dateofinvoice']= var_vat.date
        return {'value':value}
kderp_asset_management()

class kderp_asset_partial_liquidation(osv.osv):
    """This class using store partial liquidation
        Store Date, Amount, and Remark
        
        Date: 30.Jul.2014
        Author: VNDuong
    """
    _name='kderp.asset.partial.liquidation'
    _description = 'KDERP Asset - Partial Liquidation'
    _rec_name = 'date'
    
    _columns={
                'asset_id':fields.many2one('kderp.asset.management','Asset',ondelete='restrict',required=True),
                'date':fields.date('Date of Liquidation',required=True),
                'amount':fields.float('Amount',required=True),
                'remarks':fields.char('Remarks',size=128)
              }
kderp_asset_partial_liquidation()

class kderp_asset_depreciation(osv.osv): 
    _name = 'kderp.asset.depreciation'
    _description = 'KDERP Asset Depreciation'
    _auto = False
    _rec_name='expense'
        
    _columns={
                'asset_id':fields.many2one('kderp.asset.management','Asset Depreciation'),
                'expense':fields.char('Exp. Code',size=16),
                'date':fields.date('Exp. Date',readonly=True),
                'budget':fields.char('Budget',size=128),
                'amount':fields.float('Amount',readonly=True),
                'job':fields.char('Job/G.E.',size=256)
                }
    
    def init(self,cr):
        cr.execute("""
                    DROP VIEW IF EXISTS kderp_asset_depreciation;
                    Create or replace view  kderp_asset_depreciation as
                        Select
                            row_number() OVER (order by date asc, expense, asset_id) as id,
                            *
                        from
                            (select
                                koe.name as expense,
                                koe.date,
                                aaa.full_name as job,
                                abp.code || ' - ' || abp.name as budget,
                                koel.amount,
                                koel.asset_id
                            from 
                                kderp_other_expense_line koel
                            left join 
                                kderp_other_expense koe on koel.expense_id = koe.id
                            left join
                                account_analytic_account aaa on koel.account_analytic_id=aaa.id
                            left join
                                account_budget_post abp on budget_id=abp.id
                            where 
                                koe.expense_type in ('expense','monthly_expense') and koe.state not in ('cancel','draft') and coalesce(asset_id,0)>0) vwcombine""")       
kderp_asset_depreciation()

class kderp_other_expense(osv.osv):
    """
    Link Expense ID in General Expense
    """
    _name = 'kderp.other.expense'
    _inherit = 'kderp.other.expense'
    
    def _get_expense(self, cr, uid, ids, name, args, context):
        res = {}
        koe_ids = ",".join(map(str, ids))
        cr.execute("""Select 
                        koe.id,
                        kam.id 
                    from
                        kderp_other_expense koe
                    left join
                        kderp_asset_management kam on koe.id = kam.expense_id
                    where
                        koe.id in (%s) """ % koe_ids)
        for koe_id, kam_id in cr.fetchall():
            res[koe_id] = kam_id            
        return res
    
    def _get_expense_from_asset(self ,cr, uid, ids, context={}):
        res = {}
        for kam in self.pool.get('kderp.asset.management').browse(cr, uid, ids):
            if kam.expense_id:
                res[kam.expense_id.id] = True
        return res.keys()
    
    _columns = {
                'link_asset_id':fields.function(_get_expense,relation='kderp.asset.management', method = True, type='many2one', string='Asset',
                                           store ={
                                                   'kderp.asset.management':(_get_expense_from_asset, ['expense_id'], 10)})
                }