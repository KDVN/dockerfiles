import operator
import time

from osv import osv, fields
from osv.orm import intersect

import openerp.addons.decimal_precision as dp

import tools.sql
from tools import config
from tools.translate import _

import netsvc
import datetime

from openerp.tools import float_round

class kderp_contract_currency(osv.osv):
    _name = 'kderp.contract.currency'
    _desciption = "KDERP Currency System for Contract"
    
    _order = "default_curr desc"
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        unlink_ids = []

        for kccur in self.browse(cr, uid, ids):
            if kccur.default_curr:
                raise osv.except_osv("KDERP Warning","""You cannot delete an Contract Currency is Default, Please follow steps:
                                                            1. Click Discard Button.
                                                            2. Click Edit -> Uncheck default Currency, 
                                                            3. Click Save.
                                                            4. Delete Contract Currency Again !""")
            else:
                unlink_ids.append(kccur.id)

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    

    def create_currency(self,cr,uid,ctc_id,context = {}):
        curr_obj = self.pool.get('res.currency')        
        currency_ids = curr_obj.search(cr,uid,[('id','>',0)])

        new_id = False
        if not context:
            context={}
        cr.execute("""Select 
                        rcr.id,
                        rcr.name
                    from 
                        res_company rc
                    left join
                        res_currency rcr on currency_id = rcr.id""")
        curs = cr.fetchone()
        if curs:
            default_curr = curs[0]
            default_name=curs[1]
        else:
            default_curr = False
            default_name = False
        
        list_need_to_create = context.get('curr_tax_ids',[])
        
        check_default_company = False
        check_usd = False
        
        for curr_tax in list_need_to_create:
            if curr_tax['curr_name']==default_name:
                check_default_company = True
            elif curr_tax['curr_name']=='USD':
                check_usd = True
        
        if not list_need_to_create:
            list_need_to_create.append({'curr_id':default_curr,'tax_ids':[],'default_curr':True})            
        elif not check_default_company:
            list_need_to_create.append({'curr_id':default_curr,'tax_ids':[],'default_curr':False})
        
        #raise osv.except_osv("E",list_need_to_create)
        for curr in curr_obj.browse(cr,uid,currency_ids):
            if curr.name in ('USD') and not check_usd:
                new_id = self.create(cr,uid,{'name':curr.id,'rate':curr.rate,'contract_id':ctc_id,'default_curr':False,'rounding':curr.rounding,'tax_id':False})
            else:
                for lntc in list_need_to_create:
                    if curr.id==lntc['curr_id']:
                        
                        new_id = self.create(cr,uid,{'name':curr.id,'rate':curr.rate,'contract_id':ctc_id,'default_curr':lntc['default_curr'],'rounding':curr.rounding,'tax_id':[(6,0,lntc['tax_ids'])]})
        return new_id
    
    def name_search(self, cr, uid, name, args = [], operator = 'ilike', context = {}, limit = 80):
        args2 = args[:]
        if name:
            args += [('name', operator, name)]
            args += [('default_curr', '=', True)]
        if 'contract_id' in context:
            ids = []
            contract_id = context.get('contract_id',False)
            if not contract_id:
                args = [('contract_id','=',0)]
            else:
                #isinstance(contract_id,int):
                args+= [('contract_id','=',contract_id)]                
       
        ids = self.search(cr, uid, args, limit = limit)
        res = self.name_get(cr, uid, ids, context)        
        return res
    
    def _get_tax_default(self,cr,uid,context):
        tax_ids = self.pool.get('account.tax').search(cr, uid,[('type_tax_use','=','sale'),('active','=',True),('default_tax','=',True)])
        return tax_ids
    
    #Get ID Function
    ##################################
    def _get_contract(self, cr, uid, ids, context={}):
        res = {}
        for ctc in self.browse(cr,uid,ids,context):
            for ctc_line in ctc.contract_summary_currency_ids:
                res[ctc_line.id] = True
        return res.keys()
    
    def _get_quotation(self, cr, uid, ids, context={}):
        res = {}
        for so in self.browse(cr,uid,ids,context):
            if so.contract_id:
                for ctc_line in so.contract_id.contract_summary_currency_ids:
                    if ctc_line.default_curr:
                        res[ctc_line.id] = True
        return res.keys()
    
    def _get_company(self, cr, uid, ids, context={}):
        res={}
        for rp in self.browse(cr, uid, ids,context):
            cr.execute("Select id from kderp_contract_currency where coalesce(default_curr,False) and name=%s" % rp.currency_id.id)
            for id in cr.fetchall():
                res[id[0]]=True
        return res.keys()
    ##############END################
    
    def _get_special_curr(self, cr, uid, ids, name, args, context=None):
        res = {}
        if ids:
            kcc_ids = ",".join(map(str,ids))
            # Special Currency: currency=companyCurrency and default currency is true
            cr.execute("Select id, case when name=(select currency_id from res_company rc limit 1) and coalesce(default_curr,False)=True then true else false end from kderp_contract_currency kcc where kcc.id in (%s)" % kcc_ids)
            for id,sp in cr.fetchall():
                res[id]=sp or False
        return res
    
    def _get_summary_of_contract(self, cr, uid, ids, name, args, context=None):
        res={}

        if ids:
            #Tong hop amount trung voi Currency cua contract
            kcur_ids=",".join(map(str,ids))
            
            cr.execute("""Select 
                            kcc.contract_id,
                            kcc.name as currency_id,
                            sum(coalesce(price_unit,0)+coalesce(discount,0)) as subtotal,
                            (Select currency_id from res_company limit 1)=kcc.name as special
                        from 
                            kderp_contract_currency kcc
                        left join
                            res_currency rc on kcc.name = rc.id
                        left join
                            sale_order so on kcc.contract_id=so.contract_id 
                        left join
                            sale_order_line sol on so.id=sol.order_id and kcc.name=sol.currency_id and so.state='done'
                        where 
                            coalesce(kcc.contract_id,0)>0 and coalesce(default_curr,False)=True and
                            kcc.contract_id in (Select contract_id from kderp_contract_currency where id in (%s))
                        Group by
                            kcc.contract_id,
                            kcc.name;""" % kcur_ids)
            list_contract_amount={}
            special_keys={}
            for contract_id,currency_id,subtotal,special in cr.fetchall():
                list_contract_amount['%s-%s' % (contract_id,currency_id)] = {'amount':subtotal,'currency_id':currency_id,'special':special}
                if special:
                    special_keys[contract_id]='%s-%s' % (contract_id,currency_id)

            #Tong hop amount khong trung voi Currency cua contract, chuyen sang special currency
            cr.execute("""Select 
                            so.contract_id,
                            sol.currency_id as currency_id,
                            sum(coalesce(price_unit,0)+coalesce(discount,0)) as subtotal
                        from 
                            sale_order so
                        left join
                            sale_order_line sol on so.id=sol.order_id and so.state='done'
                        left join
                            kderp_contract_currency kcc on so.contract_id = kcc.contract_id and sol.currency_id=kcc.name 
                        where 
                            coalesce(so.contract_id,0)>0 and coalesce(default_curr,False)=False and 
                            so.contract_id in (Select contract_id from kderp_contract_currency kcc where kcc.id in (%s))
                        Group by
                            so.contract_id,
                            sol.currency_id""" % kcur_ids)
            
            for contract_id,currency_id,subtotal in cr.fetchall():
                if contract_id in special_keys:
                    from_amount = subtotal
                    from_curr = currency_id
                    to_currency =  list_contract_amount[special_keys[contract_id]]['currency_id']
                    new_amount = self.compute(cr, uid, from_curr, to_currency, contract_id ,from_amount)
                    #raise osv.except_osv("E",list_contract_amount['%s-%s' %(contract_id,to_currency)]['amount'] + new_amount)
                    list_contract_amount['%s-%s' %(contract_id,to_currency)]['amount'] = list_contract_amount['%s-%s' %(contract_id,to_currency)]['amount'] + new_amount
        #                       
        for kcurr in self.browse(cr,uid,ids):
            if not kcurr.default_curr:
                amount = 0.0
                tax_amount = 0.0
            else:
                #raise osv.except_osv("E",list_contract_amount['%s-%s' % (kcurr.contract_id.id,kcurr.name.id)]['amount'])
                amount=list_contract_amount['%s-%s' % (kcurr.contract_id.id,kcurr.name.id)]['amount']
                amount=float_round(amount,precision_rounding=kcurr.rounding)
                tax_amount = 0
                for tax in kcurr.tax_id:
                    if tax.type=='percent':
                        tax_amount+=float_round(amount*tax.amount,precision_rounding=kcurr.rounding)
                    elif tax.type=='fixed':
                        tax_amount+=tax.amount
            val={'amount':amount,
                 'tax_amount':tax_amount,
                 'subtotal':amount + tax_amount}
            res[kcurr.id] = val
        #raise osv.except_osv("E","E")
        return res
    
    _columns = {
             'name':fields.many2one('res.currency','Currency',required = True),
             'rate':fields.float('Ex.Rate',digits = (12,2),required = True),
             'contract_id':fields.many2one('kderp.contract.client','Contract',required=True),
             'default_curr':fields.boolean('Default'),
             'special_curr':fields.function(_get_special_curr,method=True,type='boolean',string='Special Currency',
                                            store={
                                                   'kderp.contract.currency':(lambda self, cr, uid, ids, c={}: ids, None, 20),
                                                   'res.company':(_get_company,['currency_id'],20)}),
             'rounding':fields.float('Rounding',digits = (12,6)),
             'tax_id': fields.many2many('account.tax', 'kderp_contract_tax', 'contract_currency_id', 'tax_id', 'VAT (%)', domain="[('parent_id','=',False),('type_tax_use','=','sale')]",change_default=True),
             'amount':fields.function(_get_summary_of_contract,string='Amount',type='float',digits_compute= dp.get_precision('Amount'),method=True,multi='_get_contract_currency_summary',
                                        store={
                                               'sale.order':(_get_quotation,None,20),
                                               'kderp.contract.currency':(lambda self, cr, uid, ids, c={}: ids, None, 20),
                                               'kderp.contract.client':(_get_contract,['contract_currency_ids','contract_summary_currency_ids'],20),
                                               }),
             'tax_amount':fields.function(_get_summary_of_contract,string='VAT',type='float',digits_compute= dp.get_precision('Amount'),method=True,multi='_get_contract_currency_summary',
                                        store={
                                               'sale.order':(_get_quotation,None,20),
                                               'kderp.contract.currency':(lambda self, cr, uid, ids, c={}: ids, None, 20),
                                               'kderp.contract.client':(_get_contract,['contract_currency_ids','contract_summary_currency_ids'],20),
                                               }),
             'subtotal':fields.function(_get_summary_of_contract,string='Total',type='float',digits_compute= dp.get_precision('Amount'),method=True,multi='_get_contract_currency_summary',
                                        store={
                                               'sale.order':(_get_quotation,None,20),
                                               'kderp.contract.currency':(lambda self, cr, uid, ids, c={}: ids, None, 20),
                                               'kderp.contract.client':(_get_contract,['contract_currency_ids','contract_summary_currency_ids'],20),
                                               }),
             }
    _defaults = {
        'rate': lambda *a: 0.0,
        'rounding':lambda *a:0.010000,
        'tax_id':_get_tax_default
    }
    _sql_constraints = [
        ('name_contract_currency_unique', 'unique (name,contract_id)', 'KDERP Error: The name of the currency must be unique !')
    ]
    
    def onchange_rate_name(self, cr, uid, ids, name):
        return {'value':{'name':name.upper()}}
    
    def compute(self, cr, uid, from_currency_id, to_currency_id=False,contract_id = False,amount = 1.0,context=False, round=True):
        from_rate = 0
        to_rate = 0
        rouding = 0.010000
        
        cr.execute("""Select 
                        rcr.id,
                        rcr.name
                    from 
                        res_company rc
                    left join
                        res_currency rcr on currency_id = rcr.id""")
        curs = cr.fetchone()
        if curs:
            company_curr_id = curs[0]
            company_curr_name = curs[1]
        else:
            company_curr_id = False
            company_curr_name = False
        
        from_currency_id = from_currency_id or company_curr_name
        to_currency_id = to_currency_id or company_curr_name
            
        if isinstance(from_currency_id,str) and isinstance(to_currency_id,str) and not contract_id:
            return 0
        else:
            if contract_id:
                from_currency_id = self.search(cr,uid,[('contract_id','=',contract_id),('name','=',from_currency_id)])
                if from_currency_id:
                    from_currency_id=from_currency_id[0]
                    
                to_currency_id = self.search(cr,uid,[('contract_id','=',contract_id),('name','=',to_currency_id)])
                if to_currency_id:
                    to_currency_id=to_currency_id[0]
        
        if from_currency_id:
            from_rate = self.read(cr,uid,from_currency_id,['rate'])
            if from_rate:
                from_rate = from_rate['rate']
        
        if to_currency_id:
            
            to_list = self.read(cr,uid,to_currency_id,['rate','rounding'])
            to_rate = to_list['rate']
            rounding = to_list['rounding']
            #raise osv.ex
        if to_rate:
             result = from_rate/to_rate*amount
    
        if not to_rate:
            return 0
        else:
            rate = from_rate/to_rate
            if round:
                result = float_round(amount*rate,precision_rounding=rounding)
            else:
                result = amount*rate
            
        return result
 
kderp_contract_currency()