from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from datetime import date
class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'
   
   #SYSTEM METHOD
#     def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
#         job_lists=super(account_analytic_account, self).read(cr, uid, ids, fields, context, load)
#         so_obj=self.pool.get('sale.order')
#         for job_list in job_lists:
#             if job_list.get('quotation_lists',[]):
#                 if job_list.get('job_type','E')=='E':
#                     sort_field='sort_state,q_budget_no_e,name'
#                 else:
#                     sort_field='sort_state,q_budget_no_m,name'
#                 job_list['quotation_lists']=so_obj.search(cr, uid,[('id','in',job_list.get('quotation_lists',[]))],order=sort_field)
#         return job_lists
    
    def create(self, cr, uid, vals, context=None):
        new_job_id=super(account_analytic_account, self).create(cr, uid, vals, context=context)
        kjc=self.pool.get('kderp.job.currency')
        new_id=kjc.create_currency(cr, uid, new_job_id, context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return new_job_id
    
    def write(self, cr, uid, ids, vals, context=None):
        new_obj = super(account_analytic_account, self).write(cr, uid, ids, vals, context=context)
        #cr.commit()
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return new_obj
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if not context:
            context={}
        if 'kderp_search' in context:
            kd_ctx=context['kderp_search']
            kd_ctx['id'] = kd_ctx['id'] if kd_ctx['id'] else 0
            list = self.pool.get(kd_ctx['model']).read(cr, uid, kd_ctx['id'],[kd_ctx['field']])[kd_ctx['field']]
            list_res=list
            if 'sub_model' in kd_ctx:
                list_res=[]
                for r_id in self.pool.get(kd_ctx['sub_model']).read(cr, uid, list,[kd_ctx['sub_field']]):
                    if r_id not in list_res:
                        list_res.append(r_id[kd_ctx['sub_field']][0])
            args.append((('id', 'in', list_res)))
        # Search Job cua General Expense 
        allocated_to = context.get("kderp_search_pge",[])
        if allocated_to == 'GE':
            job_ids=[]
            cr.execute("""select 
                            id  
                        from 
                            account_analytic_account
                        where 
                            general_expense""")
            for job_id in cr.fetchall():
                job_ids.append(job_id[0])
            args.append((('id', 'in', job_ids)))
        # Open Job from Quotation      
        quo_ids = context.get("kderp_search_default_quotation_lists",[])
        if quo_ids:
            job_ids=[]
            for so in self.pool.get('sale.order').browse(cr, uid, quo_ids):
                if so.job_e_id:
                    job_ids.append(so.job_e_id.id)
                if so.job_m_id:
                    job_ids.append(so.job_m_id.id)
            args.append((('id', 'in', job_ids)))  
        # Open Job from Contract
        contract_ids = context.get("kderp_search_default_contract_job_lists",[])
        if contract_ids:
            job_ids=[]
            for contract in self.pool.get('kderp.contract.client').browse(cr, uid, contract_ids):
                for so in contract.quotation_ids:
                    if so.job_e_id:
                        job_ids.append(so.job_e_id.id)
                    if so.job_m_id:
                        job_ids.append(so.job_m_id.id)
            args.append((('id', 'in', job_ids))) 
        #Open Job from Client Payment
        payment_client_ids = context.get("kderp_search_default_job_client_lists",[])
        if payment_client_ids:
            job_ids=[]
            for kcp in self.pool.get('account.invoice').browse(cr, uid, payment_client_ids):
                for kcpl in kcp.invoice_line:
                    job_ids.append(kcpl.account_analytic_id.id)
            args.append((('id', 'in', job_ids)))  
        return super(account_analytic_account, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}
        
        if context.get('current_model') == 'project.project':
            project_obj = self.pool.get("account.analytic.account")
            project_ids = project_obj.search(cr, uid, args)
            return self.name_get(cr, uid, project_ids, context=context)
        if name:
            account_ids = self.search(cr, uid, [('code', '=', name)] + args, limit=limit, context=context)
            if not account_ids:
                account_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not account_ids:
                dom = []
                for name2 in name.split('/'):
                    name = name2.strip()
                    account_ids = self.search(cr, uid, dom + [('name', 'ilike', name)] + args, limit=limit, context=context)
                    if not account_ids: break
                    dom = [('parent_id','in',account_ids)]
        else:
            account_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, account_ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        if type(ids).__name__!='list':
            ids=[ids]
                        
        if context.get('show_field',[]):
            list_field = context.get('show_field',[])
            if 'state' in list_field:
                prj_states = self.fields_get(cr, uid, ['state'],{})['state']['selection']
                prj_states = dict((x,y) for x,y in prj_states)
            for aaa in self.read(cr, uid, ids, list_field):
                display_name = ''
                aaa_id=aaa.pop('id')
                
                for f in list_field:
                    if f=='state':
                        tmp_value=prj_states[aaa[f]]
                    else:
                        tmp_value=aaa[f]    
                    if display_name:
                        display_name=display_name + " - " + tmp_value
                    else:
                        display_name= tmp_value
                res.append((aaa_id,display_name))
            return res
        
        if not context.get('show_child_parent',False):
            for aaa in self.browse(cr, uid, ids, context=context):
                res.append((aaa.id,aaa.full_name))
            return res
        
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id, self._get_one_full_name(elmt)))
        return res
    
    #FUNCTION FOR FIELD FUNCTION    
    
    def _get_job_currency(self, cr, uid, ids, name, args, context):
        res={}
        for kp in self.browse(cr, uid, ids):
            res[kp.id]=False
            for kcj in kp.job_currency_ids:
                if kcj.default_curr:
                    res[kp.id]=kcj.name.id
                    break
        return res
            
    def _get_summary_amount(self, cr, uid, ids, name, args, context):
        res={}
        kjc=self.pool.get('kderp.job.currency')
        cur_obj=self.pool.get('res.currency')
        
        for kp in self.browse(cr, uid, ids):
            job_amount=0
            job_currency=kp.job_currency
            job_amount=0
            job_tax=0
            if not job_currency:
                res[kp.id]={'job_amount':00.0,
                            'job_tax':00.0,
                            'job_total':00.0}
            else:
                for quo in kp.quotation_lists:
                    quo_sl_lists={}
                    for quo_sl in quo.quotation_submit_line:
                        if quo_sl.tax_id:
                            quo_sl_lists[quo_sl.currency_id.id]={'tax':quo_sl.tax_id,'total':quo_sl.approved_amount_e+quo_sl.approved_amount_e}
                            
                    if quo.state=='done':
                        if quo.job_e_id.id==kp.id:
                            #Thay doi o day neu muon tinh expected amount
                            for quo_line in quo.order_line:
                                quo_sl_list=quo_sl_lists.get(quo_line.currency_id.id,{})
                                tax_cal=quo_sl_list.get('tax',[])
                                total_approved_cal=quo_sl_list.get('total',0)
                                
                                job_amount+=kjc.compute(cr, uid, quo_line.currency_id.name, job_currency.name, kp.id, quo_line.price_unit+quo_line.discount)
                                for ait in tax_cal:
                                    if ait.type=='fixed':
                                        quo_per=(quo_line.price_unit+quo_line.discount)/total_approved_cal if total_approved_cal else 0
                                        job_tax+=kjc.compute(cr, uid, quo_line.currency_id.name, job_currency.name, kp.id, quo_per*(quo_line.price_unit+quo_line.discount)/100.0)
                                    elif ait.type=='percent':
                                        job_tax+=kjc.compute(cr, uid, quo_line.currency_id.name, job_currency.name, kp.id, ait.amount*(quo_line.price_unit+quo_line.discount))

                        elif quo.job_m_id.id==kp.id:
                            for quo_line in quo.order_line_m:
                                quo_sl_list=quo_sl_lists.get(quo_line.currency_id.id,{})
                                tax_cal=quo_sl_list.get('tax',[])
                                total_approved_cal=quo_sl_list.get('total',0)
                                
                                job_amount+=kjc.compute(cr, uid, quo_line.currency_id.name, job_currency.name, kp.id, quo_line.price_unit+quo_line.discount)
                                for ait in tax_cal:
                                    if ait.type=='fixed':
                                        quo_per=(quo_line.price_unit+quo_line.discount)/total_approved_cal if total_approved_cal else 0
                                        job_tax+=kjc.compute(cr, uid, quo_line.currency_id.name, job_currency.name, kp.id, quo_per*(quo_line.price_unit+quo_line.discount)/100.0)
                                    elif ait.type=='percent':
                                        job_tax+=kjc.compute(cr, uid, quo_line.currency_id.name, job_currency.name, kp.id, ait.amount*(quo_line.price_unit+quo_line.discount))
                                        
                res[kp.id]={'job_amount':job_amount,
                            'job_tax':job_tax,
                            'job_total':job_amount+job_tax}
                #raise osv.except_osv("_get_quotations_submit_link",result)
        return res
    
    def _get_total_budget(self, cr, uid, ids, name, args, context):
        res = {}
        kjc=self.pool.get('kderp.job.currency')
        for kp in self.browse(cr, uid, ids):
            total_budget=0
            for kbd in kp.kderp_budget_data_line:
                total_budget+=kbd.planned_amount
            total_budget_usd=kjc.compute(cr, uid, False, 'USD', kp.id, total_budget)

            res[kp.id]={'total_budget_amount':total_budget,
                    'total_budget_amount_usd':total_budget_usd}            
        return res
    
    def _newcode_suggest(self,cr,uid,context={}):
        list_newcode = []
        cr.execute("""Select
                        *
                    from
                        (Select * from vwnew_electrical_project_code
                        union
                        Select * from vwnew_mechanical_project_code) vwtemp
                    order by newcode""")

        for ncode,nname in cr.fetchall(): 
            list_newcode.append((ncode,ncode +": " + nname))            
        return list_newcode
    
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        val = {}
        if partner_id:
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
        result={'value':val}
        return result
    
    def onchange_suggest_code(self, cr, uid, ids,new_code):
        if new_code:
            val={'value':{'code':new_code,'newcode_suggest':False}}
        else:
            val={}
        return val
    
    def update_history(self, cr, uid, ids,context):
        for aaa in self.browse(cr,uid,ids):
           self.pool.get('kderp.budget.history').create_history(cr,uid,aaa.id)
        return True
    
    def _get_job_budget_line(self, cr, uid, ids, context=None):
        result = []
        for kbd in self.pool.get('kderp.budget.data').browse(cr, uid, ids, context=context):
            result.append(kbd.account_analytic_id.id)
        return result
    
    def _get_job_from_job_currency(self, cr, uid, ids, context=None):
        result = []
        for kcj in self.pool.get('kderp.job.currency').browse(cr, uid, ids, context=context):
            result.append(kcj.account_analytic_id.id)
        return result
    
    def _get_code_name(self, cr, uid, ids, name=None, args=None, context=None):
        if context == None:
            context = {}
        res = {}
        for aaa in self.browse(cr, uid, ids, context=context):
            res[aaa.id] = "%s - %s" % (aaa.code,aaa.name)
        return res
    
    def _get_sort(self, cr, uid, ids, name=None, args=None, context=None):
        if context == None:
            context = {}
        res = {}
        for aaa in self.browse(cr, uid, ids, context=context):
            res[aaa.id] = aaa.code[:4][2:]
        return res
    
    def _get_quotation_lists(self, cr, uid, ids, name, arg, context=None):
        res = {}
        job_ids=",".join(map(str,ids))
        
        cr.execute("""SELECT 
                        aaa.id,
                        trim(array_to_string(array_agg(so.id::text),' '))
                    FROM 
                        account_analytic_account aaa
                    left join
                        sale_order so on aaa.id=job_e_id or aaa.id=job_m_id
                    where aaa.id in (%s)
                    group by
                        aaa.id""" % (job_ids))
        for job_id,list_id in cr.fetchall():
            tmp_list=list_id
            if not tmp_list:
                tmp_list=[]
            elif tmp_list.isdigit():
                tmp_list=[int(tmp_list)]
            else:
                tmp_list=list(eval(tmp_list.strip().replace(' ',',').replace(' ','')))
            res[job_id]=tmp_list
        return res
    
    def _get_contract_lists(self, cr, uid, ids, name, arg, context=None):
        res={}
        job_ids=",".join(map(str,ids))
        
        cr.execute("""SELECT 
                        aaa.id,
                        trim(array_to_string(array_agg(so.contract_id::text),' '))
                    FROM 
                        account_analytic_account aaa
                    left join
                        sale_order so on aaa.id=job_e_id or aaa.id=job_m_id 
                    where 
                        aaa.id in (%s)
                    group by
                        aaa.id""" % (job_ids))
        for job_id,list_id in cr.fetchall():
            tmp_list=list_id
            if not tmp_list:
                tmp_list=[]
            elif tmp_list.isdigit():
                tmp_list=[int(tmp_list)]
            else:
                tmp_list=list(eval(tmp_list.strip().replace(' ',',').replace(' ','')))
            res[job_id]=list(set(tmp_list))
            
        return res

    def _get_state(self, cr, uid, ids, name, args, context=None):
        res={}
        for prj in self.browse(cr, uid, ids, context):
            res[prj.id]=prj.state
        return res
        
    def _get_actual_completion_date(self, cr, uid, ids, name, args, context=None):
        res = {}
        for prj in self.browse(cr,uid,ids, context=context):
            tmp = None
            for quo in filter(lambda qu: qu.state == 'done', prj.quotation_lists):                
                if not tmp or tmp < quo.completion_date:
                    tmp = quo.completion_date
            res[prj.id] = tmp
        return res

    def _get_quotations_link(self, cr, uid, ids, context=None):
        result = []
        for so in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
            if so.job_e_id:
                result.append(so.job_e_id.id)
            if so.job_m_id:
                result.append(so.job_m_id.id)
        return list(set(result)) #Set bo gia tri trung lap
    
    def _get_quotations_approve_link(self, cr, uid, ids, context=None):
        result = []
        for sol in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            if sol.order_id:
                if sol.order_id.job_e_id:
                    result.append(sol.order_id.job_e_id.id)
                if sol.order_id.job_m_id:
                    result.append(sol.order_id.job_m_id.id)
        return list(set(result)) #Set bo gia tri trung lap
    
    def _get_quotations_submit_link(self, cr, uid, ids, context=None):
        result = []
        for ksosl in self.pool.get('kderp.sale.order.submit.line').browse(cr, uid, ids, context=context):
            if ksosl.order_id:
                if ksosl.order_id.job_e_id:
                    result.append(ksosl.order_id.job_e_id.id)
                if ksosl.order_id.job_m_id:
                    result.append(ksosl.order_id.job_m_id.id)        
        return list(set(result))
    
    def _get_contract_link(self, cr, uid, ids, context=None):
        result = []
        for ctc in self.pool.get('kderp.contract.client').browse(cr, uid, ids, context=context):
            for so in ctc.quotation_ids:
                if so.job_e_id: 
                    result.append(so.job_e_id.id)
                if so.job_m_id:
                    result.append(so.job_m_id.id)
        return list(set(result))
    
    _rec_name='full_name'
    _order = 'sort desc,code asc, date_start desc'
    
    _columns={
                'sort':fields.function(_get_sort,size=16, type='char', string='Full Name',
                                             store={
                                                    'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['code'], 50),
                                                    }),
                'name': fields.char('Job Name', size=256, required=True,select=1),
                'full_name': fields.function(_get_code_name, type='char', string='Job',
                                             store={
                                                    'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['code','name'], 50),
                                                    }),
                
                'code': fields.char('Job No.',size=32, select=True,required=True),
                'newcode_suggest':fields.selection(_newcode_suggest,'New Code',size=16,store=False),
                
                'description': fields.text('Description'),
                
                'registration_date':fields.date('Reg. Date'),
                'date_start': fields.date('Start Date'),
                'completion_date':fields.date('Comp. Date'),
                'date': fields.date('Closed Date', select=True),
                'actual_completion_date':fields.function(_get_actual_completion_date,type='date',string='Actual Comp. Date',select=2,readonly=1,method=True,
                                                        store={
                                                              'sale.order':(_get_quotations_link, ['job_e_id','job_m_id','contract_id','state', 'completion_date'], 20)
                                                             #'kderp.contract.client':(_get_contract_link, ['completion_date'], 20)
                                                             }),

                'state': fields.selection([('doing','On-Going'),('done','Completed'),('closed','Closed'),('closed_temp','Closed (Temp.)'),('cancel','Cancelled')], "Prj. Status",required=True,select=1, track_visibility='onchange'),                
                'process_status':fields.selection([('doing','On-Going'),('done','Completed'),('closed','Closed'),('cancel','Cancelled')],"Process Status",select=1),
                
                'state_bar':fields.function(_get_state,selection=[('doing','On-Going'),('done','Completed'),('closed','Closed'),('closed_temp','Closed (Temp.)'),('cancel','Cancelled')],
                                            type='selection',method=True,string='State Bar',
                                             store={
                                                    'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['state'], 50),
                                                    }),                                
                               
                'job_type':fields.selection([('E','Electrical'),('M','Mechanical')],"E/M",select=1),
                
                'job_amount':fields.function(_get_summary_amount,string='Amount',method=True,type='float',
                                            digits_compute=dp.get_precision('Amount'),multi="_get_summary_job_amount",
                                            store={
                                                 'kderp.job.currency':(_get_job_from_job_currency, None, 20),
                                                 'sale.order':(_get_quotations_link, ['job_e_id','job_m_id','contract_id','state','order_line','order_line_m'], 20),
                                                 'sale.order.line':(_get_quotations_approve_link, None, 20),
                                                 'kderp.sale.order.submit.line':(_get_quotations_submit_link, None, 20),
                                                 }),
                
                'job_tax':fields.function(_get_summary_amount,string='VAT',method=True,type='float',
                                            digits_compute=dp.get_precision('Amount'),multi="_get_summary_job_amount",
                                            store={
                                                 'kderp.job.currency':(_get_job_from_job_currency, None, 20),
                                                 'sale.order':(_get_quotations_link, ['job_e_id','job_m_id','contract_id','state','order_line','order_line_m'], 20),
                                                 'sale.order.line':(_get_quotations_approve_link, None, 20),
                                                 'kderp.sale.order.submit.line':(_get_quotations_submit_link, None, 20),
                                                 }),
                
                'job_total':fields.function(_get_summary_amount,string='Total',method=True,type='float',
                                            digits_compute=dp.get_precision('Amount'),multi="_get_summary_job_amount",
                                            store={
                                                 'kderp.job.currency':(_get_job_from_job_currency, None, 20),
                                                 'sale.order':(_get_quotations_link, ['job_e_id','job_m_id','contract_id','state','order_line','order_line_m'], 20),
                                                 'sale.order.line':(_get_quotations_approve_link, None, 20),
                                                 'kderp.sale.order.submit.line':(_get_quotations_submit_link, None, 20),
                                                 }),
              
                'job_currency':fields.function(_get_job_currency,string='Cur.',type='many2one',method=True,relation='res.currency',
                                               store={
                                                      'kderp.job.currency':(_get_job_from_job_currency, None, 10),
                                                    }),
                'total_budget_amount':fields.function(_get_total_budget,string='Total Budget',method=True,type='float',
                                                      digits_compute=dp.get_precision('Budget'),multi='_multi_get_total_budget',
                                                      store={
                                                             'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['kderp_budget_data_line'], 20),
                                                             'kderp.budget.data':(_get_job_budget_line, ['planned_amount','budget_id','account_analytic_id'], 20)}),
              
                'total_budget_amount_usd':fields.function(_get_total_budget,string='Total Budget USD',method=True,type='float',
                                                      digits_compute=dp.get_precision('Amount'),multi='_multi_get_total_budget',
                                                      store={
                                                             'account.analytic.account':(lambda self, cr, uid, ids, c={}: ids, ['kderp_budget_data_line'], 20),
                                                             'kderp.budget.data':(_get_job_budget_line, ['planned_amount','budget_id','account_analytic_id'], 20),
                                                             'kderp.job.currency':(_get_job_from_job_currency, None, 20),
                                                             }),
              
                'contract_ids':fields.function(_get_contract_lists,relation='kderp.contract.client',type='one2many',string='Contracts',method=True),
                'quotation_lists':fields.function(_get_quotation_lists,relation='sale.order',type='one2many',string='Quotations List',method=True),
                
                #Related Fields
                'general_project_manager_id':fields.many2one("res.users",'G.P.M.',select=1),
                'user_id': fields.many2one('res.users', 'Project Manager',select=1),
                'manager_id': fields.many2one('res.users', 'Site Manager',select=1),               
                'project_manager_ref':fields.many2one("res.users",'P.M.Ref.',select=1),
                'area_site_manager_id':fields.many2one("res.users",'A.S.M.',select=1),
                
                'partner_id': fields.many2one('res.partner', 'Client',ondelete='restrict', domain="[('customer','=',1)]"),
                'owner_id':fields.many2one('res.partner','Owner',ondelete='restrict', domain="[('customer','=',1)]"),
                'address_id':fields.many2one('res.partner','Address',ondelete='restrict'),
                'invoice_address_id':fields.many2one('res.partner','Invoice Address',ondelete='restrict'),
                
                'user_related_ids': fields.many2many('res.users', 'users_projects_rel', 'pid', 'uid', 'Users'),
                'job_currency_ids':fields.one2many('kderp.job.currency','account_analytic_id','Currency System'),
                
              }
    _defaults={
               'code':lambda *x:'',
               'state':lambda *x:'doing',
               'process_status':lambda *x:'doing',
               'user_id': False,
               'date_start':False,
               "registration_date": date.today().strftime("%Y-%m-%d")
               }
    _sql_constraints = [
        ('unique_code_analytic_account', 'unique (code)',  'Job code must be unique')
    ]
    def init(self,cr):
        cr.execute("""CREATE OR REPLACE VIEW vwnew_electrical_project_code AS 
                    SELECT 
                        vwnewcode.pattern || 
                        btrim(to_char(max("substring"(vwnewcode.code::text, length(vwnewcode.pattern) + 1, 2)::integer) + 1, '00'::text)) 
                        AS newcode, vwnewcode.name
                    FROM 
                        ( 
                        SELECT isq.name, 
                                   CASE
                                        WHEN aaa.code IS NULL THEN (isq.prefix::text || to_char('now'::text::date::timestamp with time zone, ('YY-'::text || isq.suffix::text) || '00'::text))::character varying
                                        ELSE aaa.code
                                    END AS code, isq.prefix::text || to_char('now'::text::date::timestamp with time zone, 'YY-'::text || isq.suffix::text) AS pattern
                               FROM ir_sequence isq
                          LEFT JOIN account_analytic_account aaa ON aaa.code::text ~~ ((isq.prefix::text || to_char('now'::text::date::timestamp with time zone, 'YY-'::text || isq.suffix::text)) || '__'::text)
                         WHERE isq.code::text = 'kderp_electrical_project_code'::text AND isq.active) vwnewcode
                      GROUP BY vwnewcode.pattern, vwnewcode.name;
                    
                      CREATE OR REPLACE VIEW vwnew_mechanical_project_code AS 
                     SELECT vwnewcode.pattern || btrim(to_char(max("substring"(vwnewcode.code::text, length(vwnewcode.pattern) + 1, 2)::integer) + 1, '00'::text)) AS newcode, vwnewcode.name
                       FROM ( SELECT isq.name, 
                                    CASE
                                        WHEN aaa.code IS NULL THEN (isq.prefix::text || to_char('now'::text::date::timestamp with time zone, ('YY-'::text || isq.suffix::text) || '00'::text))::character varying
                                        ELSE aaa.code
                                    END AS code, isq.prefix::text || to_char('now'::text::date::timestamp with time zone, 'YY-'::text || isq.suffix::text) AS pattern
                               FROM ir_sequence isq
                          LEFT JOIN account_analytic_account aaa ON aaa.code::text ~~ ((isq.prefix::text || to_char('now'::text::date::timestamp with time zone, 'YY-'::text || isq.suffix::text)) || '__'::text)
                         WHERE isq.code::text = 'kderp_mechanical_project_code'::text AND isq.active) vwnewcode
                      GROUP BY vwnewcode.pattern, vwnewcode.name;""")
account_analytic_account()