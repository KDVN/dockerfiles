from openerp.osv import fields, osv
import time
import datetime
import openerp.addons.decimal_precision as dp

class kderp_general_expense_code(osv.osv):
    _name='kderp.general.expense.code'
    _description='KDERP General Expense Code'
    _rec_name = 'code'
    
    STATE_SELECTION=[('on-going','On-Going'),
                     ('closed','Closed'),
                 ]
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
                ctc_ids = self.search(cr, uid,[('description', 'ilike', name)] + args, limit=limit, context=context)
        else:
            ctc_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ctc_ids, context=context)   
   
    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        reads = self.read(cr, uid, ids, ['description', 'code'], context=context)
        res = []
        for record in reads:
            name = (record['code'] + ' - ' + record['description']) if record['code'] else record['description']  
                
            res.append((record['id'], name))
        return res 
    
    def _sumnary_budget(self, cr, uid, ids, name, args, context):
        res = {}
        if ids:
            gec_ids = ",".join(map(str,ids))
            cr.execute("""select kgec.id, 
                                coalesce(qr_budget_amount.budget_amount,0),
                                coalesce(expense_amount,0),
                                sum(coalesce(payment_amount,0))
                        from 
                            kderp_general_expense_code kgec
                        left join 
                            ( 
                                select general_expense_code_id ,
                                    sum(budget_amount) as budget_amount
                                from 
                                    kderp_general_expense_code_budget_data
                                    where general_expense_code_id  in (%s)
                                group by general_expense_code_id 
                            )qr_budget_amount on qr_budget_amount.general_expense_code_id=kgec.id
                        left join 
                             (
                                select kge.general_expense_code_id as general_expense_code_id ,
                                        sum(coalesce(kgel.amount,0)*coalesce(rate,0)) as expense_amount
                                from  
                                        kderp_general_expense_line kgel
                                left join 
                                        kderp_general_expense kge on kge.id=kgel.general_expense_id
                                left join 
                                        kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                where  
                                        kge.general_expense_code_id >0  and kge.state not in ('draft','cancel') and kge.type not in ('fixed-asset','prepaid') 
                                        and kge.general_expense_code_id in (%s)
                                group by 
                                        kge.general_expense_code_id
                                )qrex on qrex.general_expense_code_id =  kgec.id
                        left join 
                                ( select kge.general_expense_code_id as general_expense_code_id ,
                                        sum(coalesce(kgel.amount,0)*coalesce(rate,0))as payment_amount
                                   from  
                                        kderp_general_expense_line kgel
                                   left join 
                                        kderp_general_expense kge on kge.id=kgel.general_expense_id 
                                   left join 
                                        kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                   where 
                                         kge.type='monthly-expense' and  kge.general_expense_code_id in (%s)
                                   group by kge.general_expense_code_id
                                   union 
                                   select kge.general_expense_code_id as general_expense_code_id,
                                         sum(coalesce(kgep.amount,0)*coalesce(rate,0))
                                   from  
                                        kderp_general_expense kge
                                   left join 
                                        kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                   left join 
                                        kderp_general_expense_supplier_payment kgep on kgep.general_expense_id= kge.id
                                   where 
                                        kgep.state not in ('draft','cancel') and  kge.type='others' and kge.general_expense_code_id in (%s)
                                   group by kge.general_expense_code_id
                                 )qr_payment on qr_payment.general_expense_code_id= kgec.id           
                   where  kgec.id in(%s)  group by  kgec.id ,expense_amount ,qr_budget_amount.budget_amount                                                                  
                  """ % (gec_ids,gec_ids,gec_ids,gec_ids,gec_ids))
                                                 
            for id, total_budget,total_expense,total_payment  in cr.fetchall():
                res[id]={
                             'total_budget':total_budget,
                             'total_expense':total_expense ,
                             'total_payment':total_payment,
                             'total_budget_expense':total_budget-total_expense,
                             'total_expense_payment':total_expense-total_payment
                             }
            return res
        
    def _get_general_expense_budget_data(self, cr, uid, ids, context=None):
        res=[]
        for kebl in self.pool.get('kderp.general.expense.code.budget.data').browse(cr, uid, ids, context=context):
            for kbd in kebl.general_expense_code_id.general_expense_code_ids:
                if kbd.budget_id.id==kebl.budget_id.id:
                    res.append(kbd.id)
        return list(set(res))
    
    def _get_general_expense(self, cr, uid, ids , context):
        res = []
        if ids:
            ge_ids = ",".join(map(str,ids))
            cr.execute("""select distinct kgec.id from kderp_general_expense_code kgec 
                            left join kderp_general_expense kge on kge.general_expense_code_id=kgec.id
                            left join kderp_general_expense_code_budget_data  kgecbd on kgecbd.general_expense_code_id=kgec.id
                            left join kderp_general_expense_line kgel on kgel.general_expense_id =kge.id and kgel.budget_id = kgecbd.budget_id where kge.id in (%s)""" % ge_ids)
                                                    
            for id  in cr.fetchall():    
                res.append(id[0])
        return res
    
    def _get_general_expense_line(self, cr, uid, ids , context):
        res = []
        if ids:
            ge_ids = ",".join(map(str,ids))
            cr.execute("""select distinct kgec.id from kderp_general_expense_code kgec 
                            left join kderp_general_expense kge on kge.general_expense_code_id=kgec.id
                            left join kderp_general_expense_code_budget_data  kgecbd on kgecbd.general_expense_code_id=kgec.id
                            left join kderp_general_expense_supplier_payment kgesp on kgesp.general_expense_id=kge.id
                            left join kderp_general_expense_line kgel on kgel.general_expense_id =kge.id and kgel.budget_id = kgecbd.budget_id where kgel.id in (%s)""" % ge_ids)
                                                    
            for id  in cr.fetchall():    
                res.append(id[0])
        return res
    
    def _get_general_supplier_payment(self, cr, uid, ids , context):
        res = []
        if ids:
            gesp_ids = ",".join(map(str,ids))
            cr.execute("""select distinct kgec.id     
                        from 
                            kderp_general_expense_code kgec
                        left join 
                            kderp_general_expense kge on kge.general_expense_code_id =kgec.id
                        left join 
                            kderp_general_expense_supplier_payment kgesp on kgesp.general_expense_id =kge.id
                        where kgesp.id in (%s)""" % gesp_ids)
            for id  in cr.fetchall():    
                res.append(id[0])
        return res
    
    _columns={
               'code':fields.char('G.E.Code',size=16,required=True,select=True,states={'closed':[('readonly',True)]}),
               'description':fields.char('Description',size=128,required=True,states={'closed':[('readonly',True)]}),
               'start_date':fields.date('Start Date',states={'closed':[('readonly',True)]}),
               'end_date':fields.date('End Date',states={'closed':[('readonly',True)]}),
               'completion_date':fields.date('Completion Date',states={'closed':[('readonly',True)]}),
               'closed_date':fields.date('Closed Date',states={'closed':[('readonly',True)]}),
               'state':fields.selection(STATE_SELECTION,'GEC. Status',readonly=True,select=1,states={'closed':[('readonly',True)]}),
               'general_expense_code_currency_ids':fields.one2many('kderp.general.expense.code.currency','general_expense_code_id','Currency',ondelete="restrict",states={'closed':[('readonly',True)]}),
               'general_expense_code_ids': fields.one2many("kderp.general.expense.code.budget.data",'general_expense_code_id',string="Budget Code",ondelete="restrict",states={'closed':[('readonly',True)]}),
               'total_budget':fields.function(_sumnary_budget, digits_compute= dp.get_precision('total_budget'),string='Total Budget',type='float', method=True, multi="summary_budget",
                                                  store={   'kderp.general.expense.code':(lambda self, cr, uid, ids, c={}: ids,['general_expense_code_ids'],50),
                                                            'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','state','state'], 5),
                                                            'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount'], 5),
                                                            'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, ['budget_id', 'budget_amount','general_expense_code_id'], 10),        
                                                         }),
              'total_expense':fields.function(_sumnary_budget, digits_compute= dp.get_precision('total_expense'),string='Expense',type='float', method=True, multi="summary_budget",
                                                  store={
                                                            'kderp.general.expense.code':(lambda self, cr, uid, ids, c={}: ids,None,50),
                                                            'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','state','state'], 5),
                                                            'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount'], 5),
                                                            'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),    
                                                         }),
               'total_payment':fields.function(_sumnary_budget, digits_compute= dp.get_precision('total_payment'),string='Payment',type='float', method=True, multi="summary_budget",
                                                  store={
                                                           'kderp.general.expense.code':(lambda self, cr, uid, ids, c={}: ids,None,50) ,
                                                           'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','state'], 5),
                                                           'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount'], 5),
                                                           'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),
                                                           'kderp.general.expense.supplier.payment':(_get_general_supplier_payment,['general_expense_id','amount','state'], 5),
                            
                                                         }),
              'total_budget_expense':fields.function(_sumnary_budget, digits_compute= dp.get_precision('Balance'),string='(1)-(2)',type='float', method=True, multi="summary_budget",
                                                  store={
                                                            'kderp.general.expense.code':(lambda self, cr, uid, ids, c={}: ids,['general_expense_code_ids'],50) ,
                                                            'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','state'], 5),
                                                            'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount'], 5),
                                                            'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),                                                        
                                                         }),
              'total_expense_payment':fields.function(_sumnary_budget, digits_compute= dp.get_precision('Balance'),string='(2)-(3)',type='float', method=True, multi="summary_budget",
                                                  store={
                                                            'kderp.general.expense.code':(lambda self, cr, uid, ids, c={}: ids,None,50) ,
                                                            'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','state'], 5),
                                                            'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount'], 5),
                                                            'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),
                                                            'kderp.general.expense.supplier.payment':(_get_general_supplier_payment,['general_expense_id','amount','state'], 5),
                                                          }),
                                
              }
   
    def btn_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'closed'})
        return True
    
    def btn_re_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'on-going'})
        return True
    
    def _get_new_code(self, cr, uid, context): 
        temp_code=self.pool.get('ir.sequence').get(cr, uid, 'kderp.general.expense.code')  
        return temp_code[:len(temp_code)-1]
 
    _defaults = {
#                     'code': lambda  self, cr, uid, context:self.pool.get('ir.sequence').get(cr, uid, 'kderp.hanoi.general.expense.code')  
                    'state':lambda *x: 'on-going',
                    'code' :_get_new_code  , 
                    'total_budget':lambda *x: 0.0,
                    'total_expense':lambda *x: 0.0,
                    'total_payment':lambda *x: 0.0,
                }
    
    _sql_constraints = [('general_expense_code_unique',"unique(code)","KDERP Error: The General Expense Code must be unique !")]
  
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'on-going',
            'code':self._get_new_code(cr, uid,0)
        })
        return super(kderp_general_expense_code, self).copy(cr, uid, id, default, context)
kderp_general_expense_code()

class kderp_general_expense_code_budget_data(osv.osv):
    _name='kderp.general.expense.code.budget.data'
    _description='KDERP General Expense Code Line'
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            if not ids:
                ids = self.search(cr, user, [('general_expense_code_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('budget_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                check=name.replace(',','')
                if check.isdigit():
                    ids = self.search(cr, user, [('expense_amount','=',name)]+ args, limit=limit, context=context)            
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
   
    def _get_general_expense_budget(self, cr, uid, ids, name, args, context):
        res = {}
        balance_over_budget=self.pool.get('res.users').browse(cr,uid,uid).company_id.over_budget_value
        if ids:
            budget_data_ids = ",".join(map(str,ids))
            cr.execute("""select kbd.id ,kbd.general_expense_code_id,
                             coalesce( kbd.budget_amount,0),
                              coalesce(qrex.expense_amount,0) ,
                              sum(qr_payment.payment_amount)
                        from 
                             kderp_general_expense_code_budget_data kbd 
                        left join 
                            (select 
                                    kgel.budget_id, kge.general_expense_code_id as general_expense_code_id ,
                                    sum(coalesce(kgel.amount,0)*coalesce(rate,0)) as expense_amount
                                from  
                                    kderp_general_expense_line kgel
                                left join 
                                    kderp_general_expense kge on kge.id=kgel.general_expense_id
                                left join 
                                    kderp_general_expense_code_budget_data kbd on kbd.general_expense_code_id=kge.general_expense_code_id  and kbd.budget_id=kgel.budget_id
                                left join 
                                       kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                where  
                                      kge.general_expense_code_id >0  and kge.state not in ('draft','cancel') and kge.type not in ('fixed-asset','prepaid') and kbd.id in (%s)
                                 group by kgel.budget_id,kge.general_expense_code_id 
                                )qrex on qrex.budget_id = kbd.budget_id and qrex.general_expense_code_id=kbd.general_expense_code_id
                        left join  
                            (select kgel.budget_id, kge.general_expense_code_id as general_expense_code_id  ,sum(coalesce(kgel.amount,0)*coalesce(rate,0)) as payment_amount
                                from
                                     kderp_general_expense_line kgel
                                left join 
                                     kderp_general_expense kge on kge.id=kgel.general_expense_id
                                left join 
                                    kderp_general_expense_code_budget_data kbd on kbd.general_expense_code_id=kge.general_expense_code_id and kbd.budget_id=kgel.budget_id
                                left join 
                                    kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                where  
                                    kge.general_expense_code_id >0  and kge.state not in ('draft','cancel') and kge.type  in  ('monthly-expense') and kbd.id in(%s)
                                        group by kgel.budget_id, kbd.budget_id, kge.general_expense_code_id
                                union all
                                     select  kgel.budget_id, kge.general_expense_code_id as general_expense_code_id ,
                                        kgel.amount*
                                    case when
                                         coalesce(qr_expense.expense_amount,0)=0 then 0
                                    else
                                        sum(coalesce(kgep.amount,0)*coalesce(rate,0))/coalesce(qr_expense.expense_amount,0)*coalesce(rate,0)
                                     end as  payment_amount              
                                from  
                                    kderp_general_expense_line kgel
                                left join 
                                     kderp_general_expense kge on kge.id=kgel.general_expense_id 
                                left join kderp_general_expense_code_budget_data kbd on kbd.general_expense_code_id=kge.general_expense_code_id and kbd.budget_id=kgel.budget_id
                                left join 
                                    kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                left join 
                                    kderp_general_expense_supplier_payment kgep on kgep.general_expense_id= kge.id
                                left join 
                                        (select kge.id as general_expense_id ,
                                        sum(coalesce(kgel.amount,0)*coalesce(rate,0)) as expense_amount
                                        from  
                                            kderp_general_expense_line kgel
                                        left join 
                                            kderp_general_expense kge on kge.id=kgel.general_expense_id
                                        left join 
                                            kderp_general_expense_code_currency kcc on kcc.general_expense_code_id=kge.general_expense_code_id and kcc.name =kge.currency_id
                                         where  kge.state not in ('draft','cancel')and kge.type  in ('others')
                                                                    group by kge.id
                                        )qr_expense on qr_expense.general_expense_id=kge.id 
                              where kgep.state not in ('draft','cancel')and kge.type  in ('others') and kbd.id in (%s)
                              group by kgel.budget_id,kgel.amount,qr_expense.expense_amount  ,kge.general_expense_code_id ,kcc.rate
                            )qr_payment on qr_payment.budget_id=kbd.budget_id and qr_payment.general_expense_code_id =kbd.general_expense_code_id                
                         where  kbd.id  in (%s)         
                         group by kbd.id,kbd.general_expense_code_id ,qrex.expense_amount """ % (budget_data_ids,budget_data_ids,budget_data_ids,budget_data_ids))
            for id,general_expense_code_id, amount,expense_amount,payment_amount  in cr.fetchall():
                res[id]={
                             'expense_amount':expense_amount,
                             'payment_amount':payment_amount ,
                             'balance':amount-expense_amount,
                             'over':False if amount-expense_amount>=balance_over_budget else True
                              
                             }
            return res
#     def _get_budget_line_from_general_expense_line(self, cr, uid, ids, context=None):
#         res=[]
#         for kebl in self.pool.get('kderp.general.expense.line').browse(cr,uid,ids):
#             for kbd in kebl.general_expense_id.general_expense_code_id.general_expense_line_ids.general_expense_code_ids:
#                 if kbd.budget_id.id==kebl.budget_id.id:
#                     res.append(kbd.id)
#         return list(set(res))
    
    def _get_general_expense_budget_data(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('kderp.general.expense.code.budget.data').browse(cr, uid, ids, context=context):
            result[line.id] = True
        return result.keys()
 
    def _get_general_expense_line(self, cr, uid, ids, context=None):
        res=[]
        for kebl in self.pool.get('kderp.general.expense.line').browse(cr, uid, ids, context=context):
            for kbd in kebl.general_expense_id.general_expense_code_id.general_expense_code_ids:
                if kbd.budget_id.id==kebl.budget_id.id:
                    res.append(kbd.id)
        return list(set(res))
    
    def _get_general_expense(self, cr, uid, ids , context):
        res = []
        if ids:
            ge_ids = ",".join(map(str,ids))
            cr.execute("""select distinct kbd.id     
                        from 
                            kderp_general_expense_code_budget_data kbd 
                        left join 
                            kderp_general_expense kge on kge.general_expense_code_id =kbd.general_expense_code_id
                        left join 
                            kderp_general_expense_code kgec on kgec.id=kge.general_expense_code_id
                        left join 
                            kderp_general_expense_line kgel on kgel.general_expense_id =kge.id and kgel.budget_id=kbd.budget_id
                        left join
                            kderp_general_expense_supplier_payment kgesp on kgesp.general_expense_id =kge.id
                         where kge.id in (%s)""" % ge_ids)
                                                     
            for id  in cr.fetchall():    
                res.append(id[0])
        return res
    
    def _get_general_supplier_payment(self, cr, uid, ids , context):
        res = []
        if ids:
            gesp_ids = ",".join(map(str,ids))
            cr.execute("""select distinct kbd.id     
                        from 
                            kderp_general_expense_code_budget_data kbd 
                        left join 
                            kderp_general_expense kge on kge.general_expense_code_id =kbd.general_expense_code_id
                        left join 
                            kderp_general_expense_line kgel on kgel.general_expense_id =kge.id 
                        left join 
                            kderp_general_expense_supplier_payment kgesp on kgesp.general_expense_id =kge.id
                        where kgesp.id in (%s)""" % gesp_ids)
            for id  in cr.fetchall():    
                res.append(id[0])
        return res
    
    def _get_general_expense_code_currency(self,cr,uid,ids,context):
        res = []
        if ids:
            kgecc_ids = ",".join(map(str,ids))
            cr.execute("""select  kbd.id 
                        from kderp_general_expense_code_budget_data kbd  
                        left join 
                               kderp_general_expense_code kgec on kgec.id =kbd.general_expense_code_id
                        left join kderp_general_expense_code_currency kgecc on kgecc.general_expense_code_id=kgec.id
                        where kgecc.id in (%s)
                        """ % kgecc_ids)
            for id  in cr.fetchall():    
                res.append(id[0])
        return res
        
    _columns={  
                'general_expense_code_id':fields.many2one("kderp.general.expense.code", string="Budget Code",ondelete="restrict",readonly=True),
                'budget_id': fields.many2one("kderp.general.expense.budget.code", string="Budget Code",required=1,ondelete="restrict",select=1),
                'budget_amount':fields.float("Budget Amount",required=True),
                'expense_amount':fields.function(_get_general_expense_budget,string='Expense',digits_compute=dp.get_precision('G.E. Budget'),method=True,type='float',multi='_get_general_expense_info',
                                               store={ 
                                                      'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),                                                    
                                                      'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount','general_expense_id'], 10), 
                                                      'kderp.general.expense':(_get_general_expense,['exrate','general_expense_code_id','general_expense_code_id','state'], 5),
                                                      'kderp.general.expense.code.currency':(_get_general_expense_code_currency, None, 10),    
                                                       }), 
                'payment_amount':fields.function(_get_general_expense_budget,string='Payment',digits_compute=dp.get_precision('G.E. Budget'),method=True,type='float',multi='_get_general_expense_info',
                                               store={
                                                    'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),
                                                    'kderp.general.expense.line':(_get_general_expense_line,['budget_id','amount','general_expense_id'], 10),
                                                    'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_line_ids','general_expense_code_id','state'], 5),
                                                    'kderp.general.expense.supplier.payment':(_get_general_supplier_payment,['general_expense_id','amount','state'], 5),
                                                    'kderp.general.expense.code.currency':(_get_general_expense_code_currency, None, 10),                                                    
                                                    }), 
              
                'balance':fields.function(_get_general_expense_budget,string='Balance',digits_compute=dp.get_precision('G.E. Budget'),method=True,type='float',multi='_get_general_expense_info',
                                               store={
                                                    'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),  
                                                    'kderp.general.expense.line':(_get_general_expense_line, None, 10),
                                                    'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','general_expense_code_id','state'], 5),
                                                    'kderp.general.expense.supplier.payment':(_get_general_supplier_payment,['general_expense_id','amount','state'], 5),
                                                    'kderp.general.expense.code.currency':(_get_general_expense_code_currency, None, 10),                                                    
                                                }), 
                'over':fields.function(_get_general_expense_budget,string='Over',method=True,type='boolean',size=8,multi='_get_general_expense_info',
                                               store={
                                                    'kderp.general.expense.code.budget.data':(_get_general_expense_budget_data, None, 10),  
                                                    'kderp.general.expense.line':(_get_general_expense_line, None, 10),
                                                    'kderp.general.expense':(_get_general_expense,['currency_id','general_expense_code_id','general_expense_code_id','state'], 5),
                                                    }),
            }
    
    def btn_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'closed'})
        return True
    
    def btn_re_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'on-going'})
        return True
    
    _sql_constraints = [('budget_code',"unique(budget_id,general_expense_code_id)","KDERP Error: The General Expense Budget Data Code must be unique !")]

    _defaults={
               'payment_amount': lambda *x: 0.0,
               'expense_amount': lambda *x: 0.0,
               'balance': lambda *x: 0.0,
               'over': lambda *x:False,
               }   
    
kderp_general_expense_code_budget_data()
