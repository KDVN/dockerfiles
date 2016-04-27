import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp.tools import float_round

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_other_expense(osv.osv):
    _name = 'kderp.other.expense'
    _description = 'Other Expense for Kinden'
    
    #SYSTEM METHOD
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ots = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for ot in ots:
            if ot['state'] not in ('draft', 'cancel'):
                raise osv.except_osv("KDERP Warning",'You cannot delete an Other Expense which is not draft or cancelled.')
            else:
                unlink_ids.append(ot['id'])

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    
    def write(self, cr, uid, ids, vals, context=None):
        new_obj = super(kderp_other_expense, self).write(cr, uid, ids, vals, context=context)
        
        expense_budget_line_obj = self.pool.get('kderp.expense.budget.line')
        po_link_dicts = expense_budget_line_obj.create_update_expense_budget_line(cr,uid,ids,'kderp.other.expense','expense_id')
        if po_link_dicts:
            for koe in self.browse(cr,uid,ids):
                for koel in koe.expense_line:
                    vals1={}
                    find_keys = str(koe.id) + str(koel.account_analytic_id.id) + str(koel.budget_id.id)
                    if po_link_dicts.get(find_keys,0):
                        exp_budget_line_id = po_link_dicts.get(find_keys,0)
                        vals1['expense_budget_line'] = exp_budget_line_id
                        self.pool.get('kderp.other.expense.line').write(cr, uid, koel.id, vals1 , context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return new_obj
    
    def create(self, cr, uid, vals, context=None):
        new_obj = super(kderp_other_expense, self).create(cr, uid, vals, context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return new_obj
    
    def _get_budgets(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for exp in self.browse(cr, uid, ids):
            budgets=[]
            for line in exp.expense_line:
                budgets.append(str(line.budget_id.code))
                budgets=list(set(budgets))
            res[exp.id]=str(budgets).replace("'","").replace('[','').replace(']','')
        return res
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for exp in self.browse(cr, uid, ids, context=context):
            res[exp.id] = {
                'amount_untaxed': 0.0,
                'amount_total': 0.0,
                'amount_tax':0.0
                }
            val = 0.0
            val1=0.0
            cur = exp.currency_id
            for line in exp.expense_line:
               val += line.amount
            
            for c in self.pool.get('account.tax').compute_all(cr, uid, exp.taxes_id, val, 1, False, False)['taxes']:
                val1 += c.get('amount', 0.0)
            
            res[exp.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val)
            res[exp.id]['amount_tax']=cur_obj.round(cr, uid, cur, val1)
            
            res[exp.id]['amount_total']=res[exp.id]['amount_untaxed'] + res[exp.id]['amount_tax']
        return res
    
    def new_code(self,cr,uid,ids,job_id,order_type,name=False):
        if ids:
            try:
                ids=ids[0]
            except:
                ids=ids
        else:
            ids=0
            
        if not (order_type and job_id):
            val={'value':{'name':False}}
        else:            
            if ids:
                expense_list=self.read(cr, uid,ids,['account_analytic_id','name'])
                old_job_id=expense_list['account_analytic_id'][0]
                old_name=expense_list['name']
            else:
                old_name=False
                old_job_id=False
            
            if old_job_id==job_id and old_name:
                val={'value':{'name':old_name}}
            else:
                job_code_list=self.pool.get("account.analytic.account").read(cr,uid,job_id,['code'])
                if not job_code_list:
                    val={'value':{'name':False}}
                else:
                    job_code = job_code_list['code']
                    project_code_len = 0
                    project_code_len = len(str(job_code)+"-M")+1
                    
                    cr.execute("Select \
                                    max(substring(name from "+str(project_code_len)+" for length(name)-"+str(project_code_len-1)+"))::integer \
                                from \
                                    kderp_other_expense \
                                where name ilike '"+job_code+"-"+order_type[:1].upper()+"%' and id!="+str(ids))
                    if cr.rowcount:
                        next_code=str(cr.fetchone()[0])
                        #raise osv.except_osv("E",next_code)
                        if next_code.isdigit():
                            next_code=str(int(next_code)+1)
                        else:
                            next_code='1'
                    else:
                        next_code='1'
                    val={'value':{'name':job_code+'-'+order_type[:1].upper()+next_code.rjust(3,'0')}}
            
        return val
    
    def _get_exrate(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        company_currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        res = {}
        
        usd_id = cur_obj.search(cr, uid, [('name','=','USD')])[0]
        
        for exp in self.browse(cr,uid,ids):
            from_curr = exp.currency_id.id
            compute_date = exp.date
            exrate = cur_obj.compute(cr, uid, from_curr, company_currency_id, 1, round=False,context={'date': compute_date})
            if company_currency_id==from_curr:
                ref_exrate=cur_obj.compute(cr, uid, usd_id, from_curr, 1, round=False,context={'date': compute_date})
            else:
                ref_exrate=exrate
            res[exp.id]={'exrate':exrate,
                         'ref_exrate':ref_exrate}
        return res
    
    def _get_job(self, cr, uid, context={}):
        if not context:
            context={}
        return context.get('account_analytic_id',False)
    
    def _get_expense_from_detail(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('kderp.other.expense.line').browse(cr, uid, ids, context=context):
            result[line.expense_id.id] = True
        return result.keys()
    
    def on_changevalue(self, cr, uid, ids, amount, taxes_id, currency_id):
        amount_tax = 0.0
        if taxes_id[0][2]:
            tax_obj =self.pool.get('account.tax')

            val=0.0
            tax_brs = tax_obj.browse(cr, uid,taxes_id[0][2]) 
            for c in tax_obj.compute_all(cr, uid, tax_brs, amount, 1, False, False)['taxes']:
                val += c.get('amount', 0.0)
            
            if currency_id:
                cur_obj=self.pool.get('res.currency')
                cur_brs=cur_obj.browse(cr, uid, currency_id)
                amount_tax=cur_obj.round(cr, uid, cur_brs, val)
            else:
                amount_tax=val            
        result={'amount_tax':amount_tax,'amount_total':amount_tax+amount}
        return {'value':result}
    
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
                }}
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
        supplier = partner.browse(cr, uid, partner_id)
        return {'value': {'address_id': supplier.id or False }}
    
    def _get_tax_default(self,cr,uid,context):
        tax_ids = self.pool.get('account.tax').search(cr, uid,[('type_tax_use','=','purchase'),('active','=',True),('default_tax','=',True)])
        return tax_ids
    
    STATE_SELECTION=[('draft','Draft'),
                   ('waiting_for_payment','Waiting for Payment'),
                   ('done','Completed'),
                   ('revising','Expense Revising'),
                   ('cancel','Expense Canceled')]
    _order="date desc, name desc"
    _columns={
                #String Fields
                'name': fields.char('Expense No.', size=64, required=True, select=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'description':fields.text('Scope of Works',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                #Date Fields
                'date':fields.date('Expense Date', required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                #Function Fields
                'exrate':fields.function(_get_exrate,help='Exchange rate from currency to company currency',multi='_get_exrate',
                                         method=True,string="Ex.Rate",type='float',digits_compute=dp.get_precision('Amount')),
              
                'ref_exrate':fields.function(_get_exrate,help='Exchange rate from currency to company currency',multi='_get_exrate',
                                         method=True,string="Ex.Rate",type='float',digits_compute=dp.get_precision('Amount')),
              
                'budgets':fields.function(_get_budgets, digits_compute= dp.get_precision('Amount'),string='Budgets',size=256
                                         ,type='char', method=True,
                                          store={
                                                  'kderp.other.expense.line': (_get_expense_from_detail, ['budget_id'], 10),                                                         
                                                 }),
                              
                'amount_untaxed':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'),string='Amount',type='float', method=True, multi="kderp_expense_total",
                                                  store={
                                                          'kderp.other.expense.line': (_get_expense_from_detail, None, 10),                                                         
                                                         }),
                'amount_tax':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'),string='VAT',type='float', method=True, multi="kderp_expense_total",
                                                  store={
                                                         'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['tax_amount','currency_id','taxes_id'], 10),
                                                         'kderp.other.expense.line': (_get_expense_from_detail, None, 10),                                                         
                                                         }),
                'amount_total':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'), string='Total',type='float', method=True, multi="kderp_expense_total",
                                                store={
                                                        'kderp.other.expense': (lambda self, cr, uid, ids, c={}: ids, ['tax_amount','currency_id','taxes_id'], 10),
                                                        'kderp.other.expense.line': (_get_expense_from_detail, None, 10),
                                                       }),
                #Relation Fields
                'taxes_id': fields.many2many('account.tax', 'other_expense_vat_tax', 'other_expense_vat_id', 'tax_id', 'VAT (%)', states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'expense_line': fields.one2many('kderp.other.expense.line', 'expense_id', 'Expense Details',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'state':fields.selection(STATE_SELECTION,'Exp. Status',readonly=True,select=1),
                'account_analytic_id':fields.many2one('account.analytic.account','Job',ondelete="restrict",
                                                      states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},required=True),
                'partner_id':fields.many2one('res.partner', 'Supplier', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},change_default=True),
                'address_id':fields.many2one('res.partner', 'Address',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True, states={'draft':[('readonly',False)]}),
                'currency_id': fields.many2one("res.currency", string="Currency", required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
              }
    _defaults={
               'currency_id':lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id,
               'date': lambda *a: time.strftime('%Y-%m-%d'),
               'account_analytic_id':_get_job,
               'state':lambda *x: 'draft',
               'taxes_id':_get_tax_default
               }
    _sql_constraints = [
        ('expense_unique_no', 'unique(name)', 'Expense Number must be unique !')
        ]
     
    #Inherit Default ORM
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'name':self.new_code(cr, uid, 0, self.browse(cr, uid, id,context).account_analytic_id.id, 'E','')['value']['name']
        })
        return super(kderp_other_expense, self).copy(cr, uid, id, default, context)

    #Function to Workflow
    def action_done_revising(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'revising'})
        return True
    
    def action_revising_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'})
        return True
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def action_draft_to_waiting_for_payment(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        todo = []
        period_obj = self.pool.get('account.period')
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.expense_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a Expense without any Expense Details.'))

            period_id = exp.period_id and exp.period_id.id or False
            if not period_id:
                period_ids = period_obj.find(cr, uid, exp.date, context)
                period_id = period_ids and period_ids[0] or False
            self.write(cr, uid, [exp.id], {'state' : 'waiting_for_payment', 'period_id':period_id})
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True

    def action_expense_create_payment(self, cr, uid, ids, *args):
        res = False
        #for o in self.browse(cr, uid, ids):
        for o in self.read(cr, uid, ids,['amount_total',
                                         'expense_line',
                                         'tax_amount',
                                         'currency_id',
                                         'account_analytic_id',
                                         'description'
                                         ]):        
            if o['rop_ids']:
                self.write(cr, uid, ids, {'state':'delivered','exp_status':'waiting'})
                wf_service = netsvc.LocalService("workflow")
                try:
                    wf_service.trg_delete(uid, self._name, o['id'], cr)
                except:
                    a = True
                return True
                #raise osv.except_osv('Warning','Request of payment already exist')
            payment_details = []
            adv_amount = 0.0
            retention_amount = 0.0
            adv = 0.0
            retention = 0.0
            progress = 0.0
            for po_term in self.pool.get('kdvn.po.payment.term.line').read(cr,uid,o['order_payment_term_ids'],['type','value_amount']):
                if po_term['type']=='adv':
                    adv_amount = po_term['value_amount']*o['amount_total2']/100
                    adv = po_term['value_amount']
                elif po_term['type']=='re':
                    retention_amount = po_term['value_amount']*o['amount_total2']/100
                    retention = po_term['value_amount']
                else:                    
                    progress = po_term['value_amount']
            for po_term in self.pool.get('kdvn.po.payment.term.line').read(cr,uid,o['order_payment_term_ids'],['type','value_amount','name']):
                if po_term['type']<>'p':
                    this_tax_amount = 0.0
                    this_progress_amount = 0.0
                    if po_term['type']=='adv':
                        this_retention_amount = 0.0
                        this_adv_amount = adv_amount
                    else:
                        this_adv_amount = 0.0
                        this_retention_amount = retention_amount
                else:
                    #progress = po_term['value_amount']
                    this_tax_amount = o['tax_amount']*po_term['value_amount']/100.0
                    this_progress_amount = o['amount_total2']*po_term['value_amount']/100.0
                    this_adv_amount = - adv_amount*progress/100.0
                    this_retention_amount = - retention_amount*progress/100.0
                payment_details = []
                cr.execute("Select\
                                pol.project_id,\
                                kdvn_budget_id,\
                                abp.name as budget_name,\
                                sum(price_subtotal2)\
                            from \
                                purchase_order_line pol\
                            left join\
                                product_product pp on product_id = pp.id\
                            left join\
                                account_budget_post abp on kdvn_budget_id = abp.id\
                            where order_id=%s\
                            group by\
                                pol.project_id,\
                                kdvn_budget_id,\
                                budget_name" % (o['id']))
                for project_id,budget_id,budgetname,amount in cr.fetchall():
                #self.pool.get('purchase.order.line').read(cr,uid,o['order_line'],['product_id','project_id','product_uom','price_subtotal2','name']):
                    #pr_id = budget_id
                    #prj_id = o.project_id.id
                    #raise osv.except_osv("E","%s-%s-%s" %(adv,retention,progress))
                    payment_details.append(self.payment_detail_create(project_id,budget_id,budgetname,amount,po_term['type'],adv,retention,progress))

                if o['notes']:
                    new_description = o['notes']
                else:
                    new_description = ""
                                 
                payment = {
                    'paymentno':'',
                    'amount':this_progress_amount,
                    'tax_amount':this_tax_amount,
                    'advanced_amount':this_adv_amount,
                    'retention_amount':this_retention_amount,
                    'tax_per':int(o['tax_per']) or 0,
                    'supplier_id': o['partner_id'][0],
                    'currency_id': o['currency_id'][0],
                    'detail_ids': payment_details,
                    'order_id':o['id'], # For KDVN,
                    'project_id':o['project_id'][0],
                    'description':new_description#po_term['name'] + "\n"+  o['notes']
                    }
                #raise osv.except_osv("E",payment)
                kdvn_rop_id = self.pool.get('kdvn.request.of.payment').create(cr, uid, payment)
                self.write(cr, uid, ids, {'state':'delivered','exp_status':'waiting'})
                wf_service = netsvc.LocalService("workflow")
                try:
                    wf_service.trg_delete(uid, self._name, o['id'], cr)
                except:
                    a = True
                #    wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        return kdvn_rop_id    

kderp_other_expense()
  
class kderp_other_expense_line(osv.osv):
    _name='kderp.other.expense.line'    
    _description='Customize Detail of Other Expense for Kinden'
   
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
                check=name.replace(',','')
                if check.isdigit():
                    ids = self.search(cr, user, [('amount','=',name)]+ args, limit=limit, context=context)            
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    _columns={
            'account_analytic_id':fields.many2one("account.analytic.account",'Job',required=True,ondelete="restrict"),
            'budget_id':fields.many2one("account.budget.post", "Budget",required=True,ondelete="restrict",context={'job_id':0}),
            'name':fields.char('Description', size=128),
            'amount':fields.float('Amount',digits_compute=dp.get_precision('Amount'),required=True),
            'expense_id':fields.many2one('kderp.other.expense','Other Expense',required=True,ondelete='cascade'),
            'expense_budget_line':fields.many2one('kderp.expense.budget.line','Expense Budget Line',ondelete="set null"),
              }
    _defaults={
              'amount':lambda *x:0.0,
              'account_analytic_id':lambda obj, cr, uid, context: context.get('account_analytic_id',False),
              }

    def onchange_budget_id(self, cr, uid, ids, budget_id, context=None):
        res = {'value': {'name': ""}}
        
        if not budget_id:
            return res
        
        res['value'].update({'name': self.pool.get('account.budget.post').read(cr, uid, budget_id,['name'])['name']})
        return res   
  
kderp_other_expense_line()