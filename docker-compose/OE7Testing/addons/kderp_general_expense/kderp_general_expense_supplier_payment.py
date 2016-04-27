from openerp.osv import fields, osv
import time
import datetime
import openerp.addons.decimal_precision as dp

class kderp_general_expense_supplier_payment(osv.osv):
    _name='kderp.general.expense.supplier.payment'
    _description='KDERP General Expense Supplier Payment'
    _rec_name = 'name'
    
    STATE_SELECTION=[('draft','Draft'),
                   ('waiting_for_approved','Waiting for Approved'),
                   ('waiting_for_payment','Waiting for Payment'),
                   ('done','Done'),
                   ('revising','Revising')]
     
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        #If want to set limit please sea search product
        if not args:
            args = []
        if name:
            ids=[]
            ids = self.search(cr, user, [('name','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name',operator,name.strip())]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user,[('description', 'ilike', name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
    
    def new_code(self,cr,uid,ids,general_expense_id,name=False):
        if ids:
            try:
                ids=ids[0]
            except:
                ids=ids
        else:
            ids=0
            
        if not ( general_expense_id):
            val={'value':{'name':False}}
        else:            
            if ids:
                general_expense_list=self.read(cr, uid,ids,['general_expense_id','name'])
                old_general_expense_id= general_expense_list['general_expense_id'][0]
                old_name=general_expense_list['name']
            else:
                old_name=False
                old_general_expense_id=False
            
            if old_general_expense_id==general_expense_id and old_name:
                val={'value':{'name':old_name}}
            else:
                general_expense_list=self.pool.get("kderp.general.expense").read(cr,uid,general_expense_id,['code'])
                if not general_expense_list:
                    val={'value':{'name':False}}
                else:
                    general_expense_code = general_expense_list['code']
                    cr.execute("select max(substring( name from 8 for 11)::integer)  from kderp_general_expense_supplier_payment  \
                                where name ilike '"+general_expense_code[:3]+'P'+general_expense_code[3:5]+"%'") 
                    if cr.rowcount:
                        next_code=str(cr.fetchone()[0])
                        #raise osv.except_osv("E",next_code)
                        if next_code.isdigit():
                            next_code=str(int(next_code)+1)
                        else:
                            next_code='1'
                    else:
                        next_code='1'
                    val={'value':{'name':general_expense_code[:3]+'P'+general_expense_code[3:5]+'-'+next_code.rjust(4,'0')}}
        return val
    
    def onchange_date(self, cr, uid, ids, general_expense_id):
        
        if not ( general_expense_id):
            val={'value':{'name':False}}
        else:
            general_expense_list=self.pool.get("kderp.general.expense").read(cr,uid,general_expense_id,['code'])
            if not general_expense_list:
                    val={'value':{'name':False}}
            else:
                general_expense_code = general_expense_list['code']
                cr.execute("""select max(substring( name from 8 for 11)::integer)  
                            from kderp_general_expense_supplier_payment where name not in ('')
                            """)
                if cr.rowcount:
                    next_code=str(cr.fetchone()[0])
                    if next_code.isdigit():
                        next_code=str(int(next_code)+1)
                    else:
                        next_code='1'
                else:
                    next_code='1'
                val={'value':{'name':general_expense_code[:3]+'P'+general_expense_code[3:5]+'-'+next_code.rjust(4,'0')}}
      
        return val
    
    def on_changevalue(self, cr, uid, ids, amount,tax):
        return {'value':{'total':amount+tax}
                }
 
    
    def _total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for kgesp in self.browse(cr, uid, ids, context=context):
            res[kgesp.id] = {
                'amount': 0.0,
                'total': 0.0,
                'tax':0.0
                }
            val = val1 = 0.0
            val = kgesp.amount
            val1= kgesp.tax
            res[kgesp.id]['amount'] =  val
            res[kgesp.id]['tax'] =  val1
            res[kgesp.id]['total'] = res[kgesp.id]['amount'] + res[kgesp.id]['tax']
        return res
    
    _columns={
                'name':fields.char('Payment No.',size=16,required=True,select=True,states={'done':[('readonly',True)]}),
                'date':fields.date('R.O.P. Date',states={'done':[('readonly',True)]}),
                'description':fields.char('Description',size=128,states={'done':[('readonly',True)]}),
                'general_expense_id':fields.many2one("kderp.general.expense", domain="[('type', '<>', 'monthly-expense'),('state', '<>', 'done'),('state', '<>', 'draft')]]",string="G.E.No.",required=True,ondelete="restrict",states={'done':[('readonly',True)]}), 
                'kderp_vat_invoice_ids':fields.many2many('kderp.supplier.vat.invoice','kderp_supplier_payment_genral_expense_vat_invoice_rel', 'payment_general_expense_id', 'vat_invoice_id', 'VAT Invoices',ondelete='restrict',states={'done':[('readonly',True)]}),
                'payment_ids':fields.one2many('kderp.general.expense.supplier.payment.pay','general_expense_payment_id','Payment', readonly=True, 
                                              states={'waiting_for_payment':[('readonly',False)],
                                                      'revising':[('readonly',False)]}),
                'amount':fields.float("Amount",states={'done':[('readonly',True)]}),
                'tax':fields.float("Tax",states={'done':[('readonly',True)]} ),
               
                'total':fields.function(_total,multi='_get_total',
                                         method=True,string="Total",type='float',digits_compute=dp.get_precision('Total'),
                                         store={
                                                 'kderp.general.expense.supplier.payment': (lambda self, cr, uid, ids, c={}: ids, ['amount','tax'], 10),
                                               }
                                      ),                        
                'state':fields.selection(STATE_SELECTION,'G.E. Payment Status',readonly=True,select=1),
              }
    _defaults = {
                  'amount': lambda *x: 0.0,
                  'state':lambda *x: 'draft',
                  'name':lambda *x:"",
                }
    
    def wkf_action_draft_approved(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'waiting_for_approved'})
        return True
   
    def wkf_action_approved_wfr(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'waiting_for_payment'})
        return True
    
    def action_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'revising'})
    
    def action_close(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'done'})
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'name':self.new_code(cr, uid, 0,self.browse(cr, uid, id,context).general_expense_id.id,False)['value']['name'],
            'payment_ids':False})
        return super(kderp_general_expense_supplier_payment, self).copy(cr, uid, id, default, context)
    
    def open_general_expense_supplier_payment(self, cr, uid, ids, context=None):
        return {
            "type": "ir.actions.act_window",
            "name": "Supplier Payment",
            "res_model": 'kderp.general.expense.supplier.payment',
            "res_id": ids[0] if ids else False,
            "view_type": "form",
            "view_mode": "form",
            "target":"current",
            'context':context,
            'nodestroy': True,
            'domain': "[('id','in',%s)]" % ids
        } 
    
kderp_general_expense_supplier_payment()

