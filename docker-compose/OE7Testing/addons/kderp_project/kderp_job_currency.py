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

class kderp_job_currency(osv.osv):
    _name = 'kderp.job.currency'
    _desciption = "KDERP Currency System for Job"
    
    _order = "default_curr desc"

    def create_currency(self ,cr ,uid ,job_id ,context = {}):
        if not context: context={}
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
        
        list_need_to_create = context.get('list_create',[])
        
        check_default_company = False
        check_usd = False
        
        for curr_lst in list_need_to_create:
            if curr_lst['curr_name']==default_name:
                check_default_company = True
            elif curr_lst['curr_name']=='USD':
                check_usd = True
        
        if not list_need_to_create:
            list_need_to_create.append({'curr_id':default_curr,'default_curr':True})            
        elif not check_default_company:
            list_need_to_create.append({'curr_id':default_curr,'default_curr':False})
        
        #raise osv.except_osv("E",list_need_to_create)
        new_ids=[]
        for curr in curr_obj.browse(cr,uid,currency_ids):
            if curr.name in ('USD') and not check_usd:
                new_id = self.create(cr,uid,{'name':curr.id,'rate':curr.rate,'account_analytic_id':job_id,'default_curr':False,'rounding':curr.rounding})
                new_ids.append(new_id)
            else:
                for lntc in list_need_to_create:
                    if curr.id==lntc['curr_id']:
                        new_id = self.create(cr,uid,{'name':curr.id,'rate':curr.rate,'account_analytic_id':job_id,'default_curr':lntc['default_curr'],'rounding':curr.rounding})
                        new_ids.append(new_id)
        return new_ids
    
    def name_search(self, cr, uid, name, args = [], operator = 'ilike', context = {}, limit = 80):
        args2 = args[:]
        if name:
            args += [('name.code', operator, name)]
        if 'account_analytic_id' in context:
            ids = []
            job_id = context.get('account_analytic_id',False)
            if not job_id:
                args = [('account_analytic_id','=',0)]
            else:
                args+= [('account_analytic_id','=',job_id)]                
       
        ids = self.search(cr, uid, args, limit = limit)
        res = self.name_get(cr, uid, ids, context)        
        return res
    
    #Get ID Function
    ##################################
    
    def _get_company(self, cr, uid, ids, context={}):
        res={}
        for rp in self.browse(cr, uid, ids,context):
            cr.execute("Select id from kderp_job_currency where coalesce(default_curr,False) and name=%s" % rp.currency_id.id)
            for id in cr.fetchall():
                res[id[0]]=True
        return res.keys()
    ##############END################
    
    def _get_special_curr(self, cr, uid, ids, name, args, context=None):
        res = {}
        if ids:
            kjc_ids = ",".join(map(str,ids))
            # Special Currency: currency=companyCurrency and default currency is true
            cr.execute("Select id, case when name=(select currency_id from res_company rc limit 1) and coalesce(default_curr,False)=True then true else false end from kderp_job_currency kjc where kjc.id in (%s)" % kjc_ids)
            for id,sp in cr.fetchall():
                res[id]=sp or False
        return res
    
    _columns = {
             'name':fields.many2one('res.currency','Currency',required = True),
             'rate':fields.float('Ex.Rate',digits = (12,2),required = True),
             'account_analytic_id':fields.many2one('account.analytic.account','Job',required=True),
             'default_curr':fields.boolean('Default'),
             'special_curr':fields.function(_get_special_curr,method=True,type='boolean',string='Special Currency',
                                            store={
                                                   'kderp.job.currency':(lambda self, cr, uid, ids, c={}: ids, None, 20),
                                                   'res.company':(_get_company,['currency_id'],20)}),
             'rounding':fields.float('Rounding',digits = (12,6)),
             }
    _defaults = {
        'rate': lambda *a: 0.0,
        'rounding':lambda *a:0.010000
    }
    _sql_constraints = [
        ('name_job_currency_unique', 'unique (name,account_analytic_id)', 'KDERP Error: The name of the currency must be unique !')
    ]
    
    def onchange_rate_name(self, cr, uid, ids, name):
        return {'value':{'name':name.upper()}}
    
    def compute(self, cr, uid, from_currency_id, to_currency_id=False,job_id = False,amount = 1.0,context=False, round=True):
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
            
        if isinstance(from_currency_id,str) and isinstance(to_currency_id,str) and not job_id:
            return 0
        else:
            if job_id:
                from_currency_id = self.search(cr,uid,[('account_analytic_id','=',job_id),('name','=',from_currency_id)])
                if from_currency_id:
                    from_currency_id=from_currency_id[0]
                    
                to_currency_id = self.search(cr,uid,[('account_analytic_id','=',job_id),('name','=',to_currency_id)])
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
    
        if to_rate:
            rate = from_rate/to_rate
            if round:
                result = float_round(amount*rate,precision_rounding=rounding)
            else:
                result = amount*rate
        else:
            return 0
        
        return result
 
kderp_job_currency()