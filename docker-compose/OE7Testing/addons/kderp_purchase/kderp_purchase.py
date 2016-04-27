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

class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit ='purchase.order'
    _description = 'Purchase Order for Kinden'

    def _update_tax(self, cr, uid, ids):
        if type(ids).__name__!='list':
            ids = [ids]
        for po in self.browse(cr, uid, ids):
            if not po.tax_baseline:
                pol_ids=[]
                taxes = []
                taxes_f = []
                for tax in po.taxes_id:
                    if tax.type=='percent':
                        taxes.append(tax.id)
                    elif tax.type=='fixed':
                        taxes_f.append(tax.id)                        
                for pol in po.order_line:
                    pol_ids.append(pol.id)
                if len(pol_ids)==1:
                    taxes.extend(taxes_f)
                r = self.pool.get('purchase.order.line').write(cr, uid, pol_ids,{'taxes_id': [[6, False, taxes]]})
        return True
    
    def create(self, cr, uid, vals, context={}):
        new_po_ids = super(purchase_order, self).create(cr, uid, vals, context=context)
        #cr.commit()
        new_update_tax = self._update_tax(cr, uid, new_po_ids)
        
        if len(vals.get('purchase_payment_term_ids',[]))==0:
            kdvn_po_payment_term_line_obj=self.pool.get('kderp.po.payment.term.line')         
            kdvn_payment_line_id=kdvn_po_payment_term_line_obj.create(cr,uid,{'value_amount':100.0,'name':'100% Payment',
                                    'order_id':new_po_ids})
#         else:
#             kdvn_po_payment_term_line_obj=self.pool.get('kderp.po.payment.term.line')         
#             kdvn_payment_line_id=kdvn_po_payment_term_line_obj.create(cr,uid,{'value_amount':100.0,'name':'100% Payment',
#                                                 'order_id':new_po_ids})
        
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return new_po_ids
                 
    def write(self, cr, uid, ids, vals, context=None):
        new_obj = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        if 'taxes_id' in vals or 'tax_baseline' in vals or 'order_line' in vals:
            new_update_tax = self._update_tax(cr, uid, ids)
        
        # Ko update budget khi chi thay doi trang thai
        if ('state' in vals and len(vals.keys())>=1 and vals.get('state') in ('waiting_for_delivery','waiting_for_payment','draft')):
            return new_obj
        

        expense_budget_line_obj = self.pool.get('kderp.expense.budget.line')
        po_link_dicts = expense_budget_line_obj.create_update_expense_budget_line(cr,uid,ids,'purchase.order')
        #
        if po_link_dicts:
            #po_links_indexer=dict((po_link['po_job_budget'], i) for i, po_link in enumerate(po_link_dicts))
            #raise osv.except_osv("E",po_link_dicts)
            for po in self.browse(cr,uid,ids):
                for pol in po.order_line:
                    vals1={}
                    find_keys = str(po.id) + str(pol.account_analytic_id.id) + str(pol.budget_id.id)
                    if po_link_dicts.get(find_keys,0):
                        po_budget_line_index_id = po_link_dicts.get(find_keys,0)
                        vals1['expense_budget_line'] = po_budget_line_index_id
                        self.pool.get('purchase.order.line').write(cr, uid, pol.id, vals1 , context=context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return new_obj
        
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'final_price':0.0,
                'discount_percent':0.0
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
               val1 += line.price_subtotal
               if order.tax_baseline:
                   val+=line.tax_amount

             #Tax base on Purchase
            if not order.tax_baseline:
                for tax in order.taxes_id:
                    if tax.type=='percent':
                        val+=(val1-order.discount_amount)*tax.amount
                    elif tax.type=='fixed':
                        val+=tax.amount
                        
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['discount_percent']= order.discount_amount*100.0/val1 if val1 else 0
            res[order.id]['final_price']=cur_obj.round(cr, uid, cur, val1-order.discount_amount)
            res[order.id]['amount_total']=res[order.id]['final_price'] + res[order.id]['amount_tax']
        return res
    
    def new_code(self,cr,uid,ids,job_id,order_type,name=False):
        if ids:
            ids=ids[0]
        else:
            ids=0
        if not (order_type and job_id):
            val={'value':{'name':False}}
        else:
            job_code_list=self.pool.get("account.analytic.account").read(cr,uid,job_id,['code'])
            job_code = job_code_list['code']
            if not job_code_list:
                val={'value':{'name':False}}
            else:
                ordertypefrom_database=''
                if ids:
                    expense_list=self.read(cr, uid,ids,['account_analytic_id','name','typeoforder'])
                    old_job_id=expense_list['account_analytic_id'][0]
                    old_name=expense_list['name']
                    ordertypefrom_database=expense_list['typeoforder'][:1]
                else:
                    old_name=False
                    old_job_id=False
                    
                if old_job_id==job_id and old_name and old_name.find(job_code)>=0 and ordertypefrom_database==order_type[:1]:
                    if (name.upper().find('-'+order_type[:1].upper())>=0):
                        val={'value':{'name':name}}
                    else:
                        val={'value':{'name':old_name}}
                else:
                    #project_code_len = 0
                    project_code_len = len(str(job_code)+"-M")+1
                    
                    cr.execute("Select \
                                    max(substring(name from "+str(project_code_len)+" for length(name)-"+str(project_code_len-1)+"))::integer \
                                from \
                                    purchase_order \
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
        res = {}
        for po in self.browse(cr,uid,ids):
            company_currency = po.company_id.currency_id.id
            from_curr = po.pricelist_id.currency_id.id
            compute_date = po.date_order
            res[po.id] = cur_obj.compute(cr, uid, from_curr, company_currency, 1,round=False, context={'date': compute_date})
        return res
    
    def _get_refexrate(self, cr, uid, ids, name, args, context=None):
        cur_obj = self.pool.get('res.currency')
        company_currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        res = {}
        usd_id = cur_obj.search(cr, uid, [('name','=','USD')])[0]
        for po in self.browse(cr,uid,ids):
            from_curr = po.pricelist_id.currency_id.id
            compute_date =  po.date_order
            exrate = cur_obj.compute(cr, uid, from_curr, company_currency_id, 1, round=False,context={'date': compute_date})
            if company_currency_id==from_curr:
                ref_exrate=cur_obj.compute(cr, uid, usd_id, from_curr, 1, round=False,context={'date': compute_date})
            else:
                ref_exrate=exrate
            res[po.id]=ref_exrate
        return res
    
    def _get_job(self, cr, uid, context={}):
        if not context:
            context={}
        return context.get('account_analytic_id',False)
    
    def _get_order_from_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
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
        result={'amount_tax':amount_tax}
        return {'value':result}


    def onchange_tax_id(self, cr, uid, ids, taxes, currency_id, amount,):
        tax_amount = 0
        tax_obj = self.pool.get('account.tax')
        curr_rounding = self.pool.get('res.currency').read(cr, uid, currency_id,['rounding'])['rounding']
        for taxids in taxes:
            for tax in tax_obj.browse(cr, uid, taxids[2]):
                if tax.type=='percent':
                    tax_amount+=float_round(amount*tax.amount,precision_rounding=curr_rounding)
                elif tax.type=='fixed':
                    tax_amount+=tax.amount
        return {'value':{'tax_amount':tax_amount}}
    
    def onchange_discount(self, cr, uid, ids, discount_amount, amount_untaxed):
        return {'value':{'discount_percent':discount_amount*100.0/amount_untaxed if amount_untaxed else 0,
                        'final_price':amount_untaxed-discount_amount}}
    
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        partner = self.pool.get('res.partner')
        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
                }}
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
        supplier = partner.browse(cr, uid, partner_id)
        return {'value': {
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
            'payment_term_id': supplier.property_supplier_payment_term.id or False,
            'address_id': supplier.id or False
            }}
                
    def _get_purchase_order_attachment(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if ids:
            pn_id_list = ",".join(map(str,ids))
            cr.execute("""Select po.id as id,
                           case when sum(case when coalesce(ia.quotation_attached,False) then 1 else 0 end) >0 then 1 else 0 end as quotation_attached,
                           case when sum(case when coalesce(ia.roa_comaprison_attached,False) then 1 else 0 end) >0 then 1 else 0 end as roa_comaprison_attached,
                           case when sum(case when coalesce(ia.contract_attached,False) then 1 else 0 end) >0 then 1 else 0 end as contract_attached
                               from
                                   purchase_order po
                               left join
                                   ir_attachment ia on po.id=ia.res_id and res_model='purchase.order'
                               where
                                   po.id in (%s) 
                              group by po.id""" % (pn_id_list))
            for pnl in cr.dictfetchall():
                res[pnl.pop('id')]=pnl
        return res
    
    def _get_attachement_link(self, cr, uid, ids, context=None):
        res={}
        for att_obj in self.pool.get('ir.attachment').browse(cr,uid,ids):
            if att_obj.res_model=='purchase.order' and att_obj.res_id:
                res[att_obj.res_id] = True
        return res.keys()
    
    def _get_tax_default(self,cr,uid,context):
        tax_ids = self.pool.get('account.tax').search(cr, uid,[('type_tax_use','=','purchase'),('active','=',True),('default_tax','=',True)])
        return tax_ids
        
    STATE_SELECTION=[('draft','Draft'),
                   ('waiting_for_roa','Wating for R.O.A.'),
                   ('waiting_for_delivery','Waiting for Delivery'),
                   ('waiting_for_payment','Waiting for Payment'),
                   ('done','PO Completed'),
                   ('revising','PO Revising'),
                   ('cancel','PO Canceled')]
    
    _order='date_order desc, name desc'
    _columns={
                'name': fields.char('PO No.', size=64, required=True, select=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}, track_visibility='always'),
                'date_order':fields.date('Order Date', required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                'taxes_id': fields.many2many('account.tax', 'purchase_order_taxes', 'order_id', 'tax_id', 'Taxes',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'tax_baseline':fields.boolean('Tax base on Purchase Line',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                #'tax_amount':fields.float('VAT Amount', required=True, digits_compute=dp.get_precision('Amount'), states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                'discount_amount':fields.float("Disc. Amt.",
                                               digits_compute=dp.get_precision('Amount'),
                                               states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
              
                'discount_percent':fields.function(_amount_all, digits_compute=dp.get_precision('Percent'),string='Disc.(%)',type='float', method=True, multi="kderp_po_total",
                                                  store={
                                                          'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['discount_amount','state'], 10),
                                                          'purchase.order.line': (_get_order_from_line, None, 10),                                                         
                                                         }),
                'amount_untaxed':fields.function(_amount_all, digits_compute=dp.get_precision('Amount'),string='Offered Price',type='float', method=True, multi="kderp_po_total",
                                                  store={
                                                          'purchase.order.line': (_get_order_from_line, None, 10),
                                                          'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['discount_amount','state'], 5),                                                         
                                                         }),
                'final_price':fields.function(_amount_all, digits_compute=dp.get_precision('Amount'),string='Final Price',type='float', method=True, multi="kderp_po_total",
                                                  store={
                                                          'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['discount_amount','state'], 10),
                                                          'purchase.order.line': (_get_order_from_line, None, 10),                                                         
                                                         }),
                'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Amount'),string='VAT Amt.',type='float', method=True, multi="kderp_po_total",
                                                  store={
                                                          'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['taxes_id','discount_amount','state'], 10),
                                                          'purchase.order.line': (_get_order_from_line, None, 10),                                                         
                                                         }),                                   
                'amount_total':fields.function(_amount_all, digits_compute=dp.get_precision('Amount'), string='Total',type='float', method=True, multi="kderp_po_total",
                                                store={
                                                        'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['taxes_id','discount_amount','state'], 10),
                                                        'purchase.order.line': (_get_order_from_line, None, 10),
                                                       }),
                
                'state':fields.selection(STATE_SELECTION,'Order Status',readonly=True,select=1, track_visibility='always'),
                'typeoforder': fields.selection([('m','Material'),('s','Sub-Contractor'),('ms','Material & Sub-Contractor')],
                                                'Type of order',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},required=True),
                
                #Many2one Fileds
                'account_analytic_id':fields.many2one('account.analytic.account','Job',ondelete="restrict",
                                                      states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},required=True),
                
                #'partner_id':fields.many2one('res.partner', 'Supplier', required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},change_default=True),
                'address_id':fields.many2one('res.partner', 'Address',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                'created_uid':fields.many2one('res.users','User in charge',ondelete="restrict",states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'manager_user_id':fields.many2one('res.users','Manager',ondelete="restrict",states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True, states={'draft':[('readonly',False)]}),
                
                'incoterm_id':fields.many2one('incoterm','Incoterm',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'country_of_origin':fields.many2one('res.country','Country',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                'pricelist_id':fields.many2one('product.pricelist', 'Pricelist', domain=[('type','=','purchase')],required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]}),
                'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency",readonly=True, required=True),
                
                'origin': fields.char('Order Ref.', size=64,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'notes':fields.text('Scope of Works',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                'special_case':fields.boolean('Multi-Delivery', readonly=True, states={'draft':[('readonly',False)], 'cancel':[('readonly',True)]}),
                'without_contract':fields.boolean('Without Contract',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                #Function Fields
                'exrate':fields.function(_get_exrate,help='Exchange rate from currency to company currency',
                                         method=True,string="Ex.Rate",type='float',digits_compute=dp.get_precision('Amount')),
                'ref_exrate':fields.function(_get_refexrate,help='Exchange rate from currency to company currency',
                                         method=True,string="Ex.Rate",type='float',digits_compute=dp.get_precision('Amount')),
                
                #Attached                 
                'quotation_attached':fields.function(_get_purchase_order_attachment,method=True,string='Quotation',readonly=True,type='boolean',multi='purchase_order_attachment',
                                             store={
                                                    'purchase.order':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','quotation_attached','roa_comaprison_attached','contract_attached'],20)}),
                'roa_comaprison_attached':fields.function(_get_purchase_order_attachment,method=True,string='ROA/Comparison Sheet',readonly=True,type='boolean',multi='purchase_order_attachment',
                                             store={
                                                    'purchase.order':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','quotation_attached','roa_comaprison_attached','contract_attached'],20)}),
                'contract_attached':fields.function(_get_purchase_order_attachment,method=True,string='Contract',readonly=True,type='boolean',multi='purchase_order_attachment',
                                             store={
                                                    'purchase.order':(lambda self, cr, uid, ids, c={}: ids, None, 5),
                                                    'ir.attachment':(_get_attachement_link,['res_model','res_id','quotation_attached','roa_comaprison_attached','contract_attached'],20)}),
                #Date Area                
                'effective_date':fields.date('Effective Date',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'delivery_date':fields.date('Date of Delivery',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                #Contract to Supplier Date
                'cts_date_of_contract':fields.date('Date of contract to supplier',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'cts_date_of_submitting':fields.date('Date of Submitting',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'cts_date_of_scanned':fields.date('Date of Scanned',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'cts_date_of_sending':fields.date('Date of Sending',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'cts_date_of_receiving':fields.date('Date of Receiving',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),

                #One2Many Fields
                #'purchase_budget_line':fields.one2many('kderp.purchase.budget.line','expense_id','Purchase order'),
                'purchase_payment_term_ids':fields.one2many('kderp.po.payment.term.line','order_id','Payment Terms',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                #Disable Requirement
                'location_id': fields.many2one('stock.location', 'Destination', domain=[('usage','<>','view')], states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'done':[('readonly',True)]} ),
                'invoice_method': fields.selection([('manual','Based on Purchase Order lines'),('order','Based on generated draft invoice'),('picking','Based on incoming shipments')], 'Invoicing Control', readonly=True, states={'draft':[('readonly',False)], 'sent':[('readonly',False)]}),

              }
    _defaults={
               'created_uid':lambda obj, cr, uid, context: uid,
               'name':lambda *x:"",
               'account_analytic_id':_get_job,
               'typeoforder':lambda *x:'m',
               'tax_baseline':lambda *x:False,
               'taxes_id':_get_tax_default
               }
    _sql_constraints = [
        ('purchase_unique_no', 'unique(name)', 'PO Number must be unique !')
        ]
     
    #Inherit Default ORM
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'shipped':False,
            'invoiced':False,
            'invoice_ids': [],
            'picking_ids': [],
            'name': False
        })
        res=super(purchase_order, self).copy(cr, uid, id, default, context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return res
    
    #Delete All Line
    def action_delete_all_line(self, cr, uid, ids, context):
        pol_obj=self.pool.get('purchase.order.line')
        pol_ids = pol_obj.search(cr, uid,[('order_id','in',ids)])
        if pol_ids:
            pol_obj.unlink(cr, uid, pol_ids)
        return True 
        
    #Function to Workflow
    def action_done_revising(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'revising'})
        return True
    
    def action_revising_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'})
        return True
    
    def action_draft_to_final_quotation(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        todo = []
        period_obj = self.pool.get('account.period')
        for po in self.browse(cr, uid, ids, context=context):
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)

            period_id = po.period_id and po.period_id.id or False
            if not period_id:
                period_ids = period_obj.find(cr, uid, po.date_order, context)
                period_id = period_ids and period_ids[0] or False
            self.write(cr, uid, [po.id], {'state' : 'waiting_for_roa', 'period_id':period_id,'validator' : uid})
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        return True
    
    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        wf_service = netsvc.LocalService("workflow")
        for po_id in ids:
            try:
                wf_service.trg_delete(uid, 'purchase.order', po_id, cr)
            except:
                continue
        return True
    
    def action_cancel_draft(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            wf_service.trg_delete(uid, 'purchase.order', p_id, cr)
            wf_service.trg_create(uid, 'purchase.order', p_id, cr)
        return True

    def action_picking_create(self, cr, uid, ids, context=None):
        picking_ids = []
        for order in self.browse(cr, uid, ids):
            picking_ids.extend(self._create_pickings(cr, uid, order, order.order_line, None, context=context))

        # Must return one unique picking ID: the one to connect in the subflow of the purchase order.
        # In case of multiple (split) pickings, we should return the ID of the critical one, i.e. the
        # one that should trigger the advancement of the purchase workflow.
        # By default we will consider the first one as most important, but this behavior can be overridden.
        self.write(cr,uid,ids,{'state':'waiting_for_delivery'})
        return picking_ids[0] if picking_ids else False
purchase_order()
  
class purchase_order_line(osv.osv):
    _name='purchase.order.line'
    _inherit='purchase.order.line'
    _description='Customize Purchase Order line for Kinden'
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            if name.isdigit():
                ids = self.search(cr, user, [('sequence','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('account_analytic_id',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('budget_id',operator,name)]+ args, limit=limit, context=context)
    
            if not ids:
                ids = self.search(cr, user, [('product_id','=',name)]+ args, limit=limit, context=context)
                
            if not ids:
                ids = self.search(cr, user, [('product_id',operator,name)]+ args, limit=limit, context=context)
                
            if not ids:
                ids = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
            
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    def _get_product_qty(self, cr, uid, ids, fileds, arg, context=None):
        res = {}
        pol_list=[]
        for pol in self.browse(cr, uid, ids, context=context):
            if pol.order_id.special_case:
                ################
                #Later Get from Stock Move 
                #################
                pol_list.append(pol.id)
                res[pol.id]=0
            else:
                res[pol.id] = pol.plan_qty
        if pol_list:                
            pol_ids=",".join(map(str,pol_list))
            cr.execute("""select 
                            pol.id,
                            sum(coalesce(sm.product_qty,0))
                        from 
                            purchase_order_line pol
                        left join
                            stock_move sm on pol.id=purchase_line_id
                        left join
                            stock_picking sp on sm.picking_id=sm.id
                        where
                            sp.state not in ('draft','cancel') and pol.id in (%s)
                        Group by pol.id""" % (pol_ids))
            for id,qty in cr.fetchall():
                res[id]=qty
        return res
    
    def _get_budget(self, cr, uid, ids, fields, arg, context={}):
        res={}
        for pol in self.browse(cr, uid, ids, context):
            res[pol.id]=pol.product_id.budget_id.id if pol.product_id.budget_id else False
        return res
    
    def _amount_in_company_curr(self, cr, uid, ids, fields, arg, context={}):
        res={}
        cur_obj=self.pool.get('res.currency')
        company_currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        
        for pol in self.browse(cr, uid, ids):
            try:
                if pol.order_id.state=='done' and pol.order_id.pricelist_id.currency_id<>company_currency_id:
                    res[pol.id]=cur_obj.round(cr, uid, pol.order_id.pricelist_id.currency_id,pol.final_subtotal*pol.order_id.exrate)
                else:
                    res[pol.id]=cur_obj.round(cr, uid, pol.order_id.pricelist_id.currency_id,pol.final_subtotal)
            except:
                res[pol.id]=0
        return res
            
    def _amount_all_in_line(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        
        cur_obj=self.pool.get('res.currency') 
        for pol in self.browse(cr, uid, ids, context=context):
            res[pol.id] = {
                'price_subtotal': 0.0,
                'discount_percent': 0.0,
                'final_subtotal':0.0,
                'final_total':0.0,
                'amount_tax':0.0
            }
            val = 0.0
            try:
                cur = pol.order_id.pricelist_id.currency_id
            except:
                res[pol.id]['price_subtotal']=0                    
                res[pol.id]['amount_tax']=0
                res[pol.id]['discount_percent']=0
                res[pol.id]['final_subtotal']=0
                res[pol.id]['final_total']=0
                continue
            if pol.order_id.special_case and pol.order_id.state!='done':
                price_subtotal=pol.plan_qty*pol.price_unit
            else:
                price_subtotal=pol.product_qty*pol.price_unit

            #Check if zero
            if pol.order_id.amount_untaxed:
                discount_percent = pol.order_id.discount_amount*100.0/pol.order_id.amount_untaxed
                final_subtotal = price_subtotal*(1-pol.order_id.discount_amount/pol.order_id.amount_untaxed)
            else:
                discount_percent = 0.0
                final_subtotal = price_subtotal
            
            for c in self.pool.get('account.tax').compute_all(cr, uid, pol.taxes_id, final_subtotal, 1, pol.product_id, pol.order_id.partner_id)['taxes']:
                val += c.get('amount', 0.0)

            res[pol.id]['price_subtotal']=cur_obj.round(cr, uid, cur, price_subtotal)                    
            res[pol.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[pol.id]['discount_percent']=discount_percent
            res[pol.id]['final_subtotal']=final_subtotal #Offered Price/(1-Discount Percent on PO)
            res[pol.id]['final_total']=res[pol.id]['final_subtotal'] + res[pol.id]['amount_tax']
            
        return res
      
    def _get_new_seq(self, cr, uid, context={}):
        from kderp_base import kderp_base
        if not context:
            context={}
        new_val = kderp_base.get_new_from_tree(cr, uid, context.get('id',False), self,context.get('lines',[]),'sequence', 1, 1, context)
        return new_val
    
    def _get_new_uom(self, cr, uid, context={}):
        if not context:
            context={}
        product_uom = self.pool.get('product.uom')
        new_ids=product_uom.search(cr, uid, [('name','=','pcs')])
        if new_ids:
            return new_ids[0]
        else:
            return False    
    
    def _get_line_from_order(self, cr, uid, ids, context=None):
        result = {}
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for line in po.order_line: 
                result[line.id] = True
        return result.keys()      

    def _get_line_from_picking(self, cr, uid, ids, context=None):
        result = {}
        for sp in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
            if sp.purchase_id:
                for pol in sp.purchase_id.order_line:  
                    result[pol.id] = True
        return result.keys()
    
    def _get_line_from_move(self, cr, uid, ids, context=None):
        result = {}
        for sm in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if sm.purchase_line_id:
                result[sm.purchase_line_id.id] = True
        return result.keys()
      
    def _get_line_from_product(self, cr, uid, ids, context=None):
        result = {}
        #for pp in self.pool.get('product.product').browse(cr, uid, ids, context=context):
        cr.execute("Select id,product_id from purchase_order_line pol where product_id in (%s )" % ",".join.map(str,ids))
        for pol_id,ppid in cr.fetchall():
            result[pol_id] = True
        return result.keys()
    
    def _get_line_from_order_line(self, cr, uid, ids, context=None):
        result = {}
        for pol in self.browse(cr, uid, ids, context=context):
            for poll in pol.order_id.order_line: 
                result[poll.id] = True
        return result.keys()
    
    
    _columns={
            'account_analytic_id':fields.many2one("account.analytic.account",'Job',required=1,ondelete="restrict",select=1),
            'product_uom': fields.many2one('product.uom', 'Unit', required=True),
            'product_id': fields.many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True,required=1,ondelete="restrict",select=1),
            #'budget_id': fields.related('product_id', 'budget_id', type="many2one", ,readonly=True, required=True),
            'budget_id':fields.function(_get_budget,type='many2one',relation="account.budget.post", string="Budget",select=1,
                                        store={
                                               'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['product_id'], 5),
                                               'product_product':(_get_line_from_product,['budget_id'],10)
                                               }),
            'sequence':fields.integer("Seq."),
            #'product_qty': fields.float('Qty.', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
            'plan_qty': fields.float('Plan Qty.', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
            'date_planned': fields.date('Scheduled Date', select=True),
            'brand_name':fields.many2one('kderp.brand.name','Brand'),
            
            'product_qty': fields.function(_get_product_qty,type='float',string='Qty.',method=True,
                                           digits_compute=dp.get_precision('Product Unit of Measure'),
                                           store={
                                                    'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['plan_qty'], 1),
                                                    'purchase.order': (_get_line_from_order, ['special_case','state'], 1),
                                                    'stock.picking':(_get_line_from_picking, None, 1),
                                                    'stock.move':(_get_line_from_move, None, 1),
                                                    }),
            'price_subtotal':fields.function(_amount_all_in_line,
                                             digits_compute=dp.get_precision('Amount'),string='Offered',type='float',
                                             method=True, multi="kderp_pol_total",
                                             store={
                                                    'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['price_unit','plan_qty'], 5),
                                                    'purchase.order': (_get_line_from_order, ['discount_amount','special_case','state'], 5),
                                                    }),
            'discount_percent':fields.function(_amount_all_in_line,
                                                 digits_compute=dp.get_precision('Amount'),string='Disc. Per',type='float',
                                                 method=True, multi="kderp_pol_total",
                                                 store={
                                                        'purchase.order.line': (lambda self, cr, uid, ids, c={}: ids, ['plan_qty','price_unit'], 15),
                                                        'purchase.order': (_get_line_from_order, ['discount_amount','special_case','state'], 15),
                                                        }),
            'final_subtotal':fields.function(_amount_all_in_line,string='Final',digits_compute=dp.get_precision('Percent'),type='float',
                                                 method=True, multi="kderp_pol_total",
                                                 store={
                                                        'purchase.order.line': (_get_line_from_order_line, ['price_unit','plan_qty'], 15),
                                                        'purchase.order': (_get_line_from_order, ['discount_amount','special_case','state'], 15),
                                                        }),#,digits_compute=dp.get_precision('Amount')
            'amount_tax':fields.function(_amount_all_in_line,
                                                 digits_compute=dp.get_precision('Amount'),string='VAT',type='float',
                                                 method=True, multi="kderp_pol_total",
                                                 store={
                                                        'purchase.order.line': (_get_line_from_order_line, ['plan_qty','price_unit','taxes_id'], 15),
                                                        'purchase.order': (_get_line_from_order, ['discount_amount','special_case','state','taxes_id'], 15),
                                                        }),
            'final_total':fields.function(_amount_all_in_line,
                                                 digits_compute=dp.get_precision('Amount'),string='Total',type='float',
                                                 method=True, multi="kderp_pol_total",
                                                 store={
                                                        'purchase.order.line': (_get_line_from_order_line, ['plan_qty','price_unit','taxes_id'], 15),
                                                        'purchase.order': (_get_line_from_order, ['discount_amount','special_case','state'], 15),
                                                        }),
                            
            'amount_company_curr':fields.function(_amount_in_company_curr,digits_compute=dp.get_precision('Budget'),string='Subtotal',
                                                  type='float',method=True,
                                                  store={
                                                        'purchase.order.line': (_get_line_from_order_line, ['price_unit','plan_qty'], 35),
                                                        'purchase.order': (_get_line_from_order, ['currency_id','date_order','state','discount_amount'], 35),
                                                        }),
              }
    _defaults={
              'sequence':_get_new_seq,
              'product_uom':_get_new_uom,
              'account_analytic_id':lambda obj, cr, uid, context: context.get('account_analytic_id',False),              
              }
          
    def action_confirm(self, cr, uid, ids, context=None):
        vals = {'state': 'confirmed'}
        if not context:
            context={}        
        self.write(cr, uid, ids, vals , context=context)
        return True
    
    def onchange_pol_price_qty(self, cr, uid, ids, plan_qty,price_unit):
        return {'value':{'price_subtotal':plan_qty*price_unit}}
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
  
        res = {'value': {'price_unit': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            return res
  
        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_supplierinfo = self.pool.get('product.supplierinfo')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')
  
        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))
  
        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name:
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner,from_obj='pol')[0]
            if product.description_purchase:
                name = product.description_purchase
        res['value'].update({'name': name})
  
        # - set a domain on product_uom
#        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}
  
        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id
  
#         if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
#             if self._check_product_uom_group(cr, uid, context=context):
#                 res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
#             uom_id = product_uom_po_id
  
        res['value'].update({'product_uom': uom_id})
  
        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.date.context_today(self,cr,uid,context=context)
  
  
        supplierinfo = False
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if (qty or 0.0) < min_qty: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})
  
        # - determine price_unit and taxes_id
        price=price_unit
        if pricelist_id and not price_unit:
            price = product_pricelist.price_get(cr, uid, [pricelist_id],
                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order})[pricelist_id]
        elif not price_unit:
            price = product.standard_price
  
        taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})
  
        return res   
  
purchase_order_line()