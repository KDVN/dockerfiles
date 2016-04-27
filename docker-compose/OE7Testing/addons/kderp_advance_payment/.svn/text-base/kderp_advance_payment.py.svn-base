# -*- coding: utf-8 -*-
import time
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp.tools import float_round

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler

import openerp.addons.decimal_precision as dp

try:
    from kderp_base.amount_to_text import *
except:
    pass

class kderp_advance_payment(osv.osv):
    _name = 'kderp.advance.payment'
    _description = 'KDERP Advance Payment for Kinden'
    
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    #SYSTEM METHOD
    def read(self, cr, uid, ids, fields_to_read=None, context=None, load='_classic_read'):
        self.pool.get('ir.rule').clear_cache(cr,uid)
        if isinstance(ids, (int, long)):
            ids = [ids]
        return super(kderp_advance_payment, self).read(cr, uid, ids, fields_to_read, context, load)
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        kaps = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for kap in kaps:
            if kap['state'] not in ('draft', 'cancel'):
                raise osv.except_osv("KDERP Warning",'You cannot delete an Advance Payment which is not draft or cancelled.')
            else:
                unlink_ids.append(kap['id'])

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        kcp_ids=[]
        kcp_obj=self.pool.get('kderp.cash.period')
        Update=False
        if 'date_received_money' in vals or 'date_of_received_reimbursement' in vals or 'advance_line' in vals or 'state' in vals or 'reimbursement_line' in vals or 'cash_line' in vals:
            Update=True
            for kapl in self.browse(cr, uid, ids,context):            
                kcp_ids.extend(kcp_obj.find(cr, uid, kapl.date_received_money, context))
                kcp_ids.extend(kcp_obj.find(cr, uid, kapl.date_of_received_reimbursement, context))
#                 for kaplcl in kapl.cash_line:
#                     kcp_ids.extend(kcp_obj.find(cr, uid, kaplcl.date, context))
#                 for kaplrl in kapl.reimbursement_line:
#                     kcp_ids.extend(kcp_obj.find(cr, uid, kaplrl.date, context))
                    
        new_obj = super(kderp_advance_payment, self).write(cr, uid, ids, vals, context=context)
        
        if Update:
            for kapl in self.browse(cr, uid, ids,context):            
                kcp_ids.extend(kcp_obj.find(cr, uid, kapl.date_received_money, context))
                kcp_ids.extend(kcp_obj.find(cr, uid, kapl.date_of_received_reimbursement, context))
#                 for kaplcl in kapl.cash_line:
#                     kcp_ids.extend(kcp_obj.find(cr, uid, kaplcl.date, context))
#                 for kaplrl in kapl.reimbursement_line:
#                     kcp_ids.extend(kcp_obj.find(cr, uid, kaplrl.date, context))
                    
        if len(list(set(kcp_ids)))>0:
            kcp_obj.write(cr, uid, list(set(kcp_ids)), {}, context)                
        return new_obj
    
    def _amount_to_word(self, cr, uid, ids, name, args, context={}):
        res = {}
        for x in self.browse(cr,uid,ids, context=context):
            request_amount=x.request_amount if x.request_amount>=0 else 0
            if x.currency_id.name=='USD':
                amount_to_word_vn = amount_to_text(request_amount,'vn',u" \u0111\xf4la",decimal="cents").capitalize()
                amount_to_word_en = amount_to_text(request_amount,'en'," dollar").capitalize()
            elif x.currency_id.name=='VND':
                amount_to_word_vn = amount_to_text(request_amount,'vn', u' \u0111\u1ed3ng').capitalize()  # + x.currency_id.name
                amount_to_word_en = amount_to_text(request_amount,"en","dongs").capitalize()
            else:
                amount_to_word_vn =amount_to_text(request_amount,'vn'," " + x.currency_id.name).capitalize()
                amount_to_word_en =amount_to_text(request_amount,'en'," "+ x.currency_id.name).capitalize() 
            res[x.id] = {'request_amount_to_word_vn':amount_to_word_vn,
                         'request_amount_to_word_en':amount_to_word_en}
        return res
    
    def _voucher_amount_to_word(self, cr, uid, ids, name, args, context={}):
        res = {}
        for x in self.browse(cr,uid,ids, context=context):
            reimbursement_amount=x.reimbursement_amount if x.reimbursement_amount>=0 else 0
            if x.currency_id.name=='USD':
                amount_to_word_vn = amount_to_text(reimbursement_amount,'vn',u" \u0111\xf4la",decimal="cents").capitalize()
                amount_to_word_en = amount_to_text(reimbursement_amount,'en'," dollar").capitalize()
            elif x.currency_id.name=='VND':
                amount_to_word_vn = amount_to_text(reimbursement_amount,'vn', u' \u0111\u1ed3ng').capitalize()  # + x.currency_id.name
                amount_to_word_en = amount_to_text(reimbursement_amount,"en","dongs").capitalize()
            else:
                amount_to_word_vn =amount_to_text(reimbursement_amount,'vn'," " + x.currency_id.name).capitalize()
                amount_to_word_en =amount_to_text(reimbursement_amount,'en'," "+ x.currency_id.name).capitalize() 
            res[x.id] = {'total_voucher_amount_to_word_vn':amount_to_word_vn,
                         'total_voucher_amount_to_word_en':amount_to_word_en}
        return res
                
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        #cur_obj=self.pool.get('res.currency')
        for adv in self.browse(cr, uid, ids, context=context):
            
            val = 0.0

            #cur = adv.currency_id
            for line in adv.advance_line:
                val += line.amount
            
            rb=False
            reimbursement_amount=0.0
            if adv.type_cash=='cash':
                rb=True
            else:
                if adv.state not in ('draft','approved'):
                    rb=True
                    
            for liner in adv.reimbursement_line:
                reimbursement_amount+=liner.amount
                rb=True
            if rb:
                request_amount=val            
                cash_return=request_amount-reimbursement_amount if request_amount-reimbursement_amount>0 else 0
                cash_payment=reimbursement_amount-request_amount if request_amount-reimbursement_amount<0 else 0
                balance=request_amount - (reimbursement_amount + cash_return - cash_payment)
            else:
                request_amount = val            
                cash_return = 0
                cash_payment = 0
                balance = request_amount
            
            res[adv.id]={'request_amount':request_amount,
                         'cash_return':cash_return,
                         'cash_payment':cash_payment,
                         'balance':balance,
                         'reimbursement_amount':reimbursement_amount
                         } 
        return res

    def _get_voucher_from_line(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        adv_ids = ",".join(map(str,ids))
        cr.execute("""Select 
                            kap.id,
                            array_to_string(array_agg(krb.voucher_no),E'\n')
                        from
                            kderp_advance_payment kap
                        left join    
                            kderp_advance_payment_reimbursement_line krb on kap.id = krb.advance_id
                        where 
                            kap.id in (%s)
                        group by
                            kap.id""" % (adv_ids))

        for adv_id,pvns in cr.fetchall():
            res[adv_id]=pvns
        return res
    
    def _get_outstanding(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        adv_ids = ",".join(map(str,ids))
        cr.execute("""Select 
                        user_id
                    from 
                        kderp_advance_payment kap 
                    where
                        user_id in (Select distinct user_id from kderp_advance_payment where id in (%s)) and
                        state='approved' and advance_buying<>'cash'
                    group by
                        user_id
                    having 
                        count(id)>=3""" % (adv_ids))
        list_user_standing=[]
        for u_id in cr.fetchall():
            list_user_standing.append(u_id[0])

        for adv_obj in self.browse(cr, uid, ids):
            res[adv_obj.id]=True if (adv_obj.user_id.id in list_user_standing and adv_obj.state=='approved') else False
        return res
    
#     def _get_cash_period(self, cr, uid, ids, field_name, arg, context=None):
#         if not context:
#             context={}
#         res={}
#         kcp_obj=self.pool.get('kderp.cash.period')
#         for kap in self.browse(cr, uid, ids):
#             res[kap.id]=kcp_obj.find(cr, uid, kap.date)
#         return res    
    def get_new_voucher(self, cr, uid, ids, date_received_money,payment_voucher_no,date_of_received_reimbursement,receive_voucher_no,currency,type,type_cash='payment'):
        result={}
        PT='PT'
        PC='PC'
        if not currency or type=='cash':
            return {'value':result}
        else:
            location_list={'hanoi':'HN','hcm':'SG','haiphong':'HP','all':'HN','':'HN'}
            curr=self.pool.get("res.currency").browse(cr, uid, currency).name[:1]
            location = self.pool.get('res.users').browse(cr, uid, uid).location_user
            result={}
            import datetime
            if date_received_money:                #PC V 01/14 HN 0
                ignore = False
                try:                    
                    ignore=eval(payment_voucher_no[payment_voucher_no.rfind('-')+1:])>0
                except:
                    ignore = False
                    
                if not ignore:            
                    date_received= datetime.datetime.strptime(date_received_money,"%Y-%m-%d")
                    if type=='typeCash' and type_cash=='receive':#Truong hop thu tien mat (Cash)
                        new_pc_pt ='%s%s%s-%s-' % (PT,curr,date_received.strftime('%m/%y'),location_list[location])
                    else:
                        new_pc_pt ='%s%s%s-%s-' % (PC,curr,date_received.strftime('%m/%y'),location_list[location])
                    result.update({'payment_voucher_no':new_pc_pt})
                    
            if date_of_received_reimbursement:
                ignore = False
                try:                    
                    ignore=eval(receive_voucher_no[receive_voucher_no.rfind('-')+1:])>0
                except:
                    ignore = False
                    
                if not ignore:
                    date_of_received_reimbursement=datetime.datetime.strptime(date_of_received_reimbursement,"%Y-%m-%d")
                    new_pc_pt ='%s%s%s-%s-' % (PT,curr,date_of_received_reimbursement.strftime('%m/%y'),location_list[location])
                    result.update({'receive_voucher_no':new_pc_pt})
        return {'value':result}
    
    def new_code(self,cr,uid,ids,staff_id,name=False,type='material'):
        if ids:
            try:
                ids=ids[0]
            except:
                ids=ids
        else:
            ids=0
        
        if (not staff_id):
            val={'value':{'name':False,'outstanding':False}}
        else:
            location = self.pool.get('res.users').browse(cr, uid, uid).location_user
            
            if location=='haiphong':
                location_code='P'
            elif location=='hcm':
                location_code='S'
            else:                
                location_code='H'
            
            cr.execute("""Select %s in 
                                    (Select 
                                            distinct user_id 
                                    from 
                                        kderp_advance_payment where state='approved' and advance_buying<>'cash'
                                    group by
                                        user_id
                                    having 
                                        count(id)>=3)""" % staff_id)
            if cr.fetchone()[0]:
                outstanding=True
            else:
                outstanding=False
                
            staff_code_list=self.pool.get("hr.employee").read(cr,uid,staff_id,['staffno'])
            if not staff_code_list:
                val={'value':{'name':False}}
            else:
                if type=='cash':
                    staff_code = staff_code_list['staffno'][1:]
    
                    prefix = len('C%s13-2009-X' % location_code) 
                    
                    cr.execute("Select \
                                    max(substring(name from "+str(prefix)+" for length(name)-"+str(prefix-1)+"))::integer \
                                from \
                                    kderp_advance_payment \
                                where name ilike 'C" + location_code + time.strftime('%y')+"-"+staff_code+"-"+"%%' and id!="+str(ids))
                    if cr.rowcount:
                        next_code=str(cr.fetchone()[0])
                        #raise osv.except_osv("E",next_code)
                        if next_code.isdigit():
                            next_code=str(int(next_code)+1)
                        else:
                            next_code='1'
                    else:
                        next_code='1'
                    val={'value':{'outstanding':False,'name':'C%s%s-%s-%s' %(location_code,time.strftime('%y'),staff_code,next_code.rjust(2,'0'))}}
                else:
                    staff_code = staff_code_list['staffno'][1:]
                    if name:
                        if staff_code.find(staff_code)>0:
                            return {'value':{'outstanding':outstanding}}
    
                    prefix = len('AD%s13-2009-X' % location_code) 
                    
                    cr.execute("Select \
                                    max(substring(name from "+str(prefix)+" for length(name)-"+str(prefix-1)+"))::integer \
                                from \
                                    kderp_advance_payment \
                                where name ilike 'AD" +  location_code +time.strftime('%y')+"-"+staff_code+"-"+"%%' and id!="+str(ids))
                    if cr.rowcount:
                        next_code=str(cr.fetchone()[0])
                        #raise osv.except_osv("E",next_code)
                        if next_code.isdigit():
                            next_code=str(int(next_code)+1)
                        else:
                            next_code='1'
                    else:
                        next_code='1'
                    val={'value':{'outstanding':outstanding,'name':'AD%s%s-%s-%s' % (location_code,time.strftime('%y'),staff_code,next_code.rjust(2,'0'))}}
                            
        return val
        
    def _get_job(self, cr, uid, context={}):
        if not context:
            context={}
        return context.get('account_analytic_id',False)
    
    def _get_adv_from_adv(self, cr, uid, ids, context=None):

        result = {}
        adv_ids=",".join(map(str,ids))
        cr.execute("""Select 
                            id 
                        from 
                            kderp_advance_payment 
                        where
                            state!='cancel' and state!='done' and 
                            user_id in (Select user_id from kderp_advance_payment where id in (%s)) """ % adv_ids)
        res_adv_ids=[]
        for adv_id in cr.fetchall():
            res_adv_ids.append(adv_id[0])
        res_adv_ids.extend(ids)

        return list(set(res_adv_ids))
    
    def _get_adv_from_detail(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('kderp.advance.payment.line').browse(cr, uid, ids, context=context):
            result[line.advance_id.id] = True
        return result.keys()
    
    def _get_adv_from_reimbursement_detail(self, cr, uid, ids, context=None):
        result = {}
        for liner in self.pool.get('kderp.advance.payment.reimbursement.line').browse(cr, uid, ids, context=context):
            result[liner.advance_id.id] = True
        return result.keys()    
    
    def on_changevalue(self, cr, uid, ids, amount, taxes_id, currency_id):
        amount_tax = 0.0
        result={'amount_tax':amount_tax,'amount_total':amount_tax+amount}
        return {'value':result}
    
    def _get_state(self, cr, uid, ids, name, args, context=None):
        res={}
        for adv in self.browse(cr, uid, ids, context):
            res[adv.id]=adv.state
        return res
    
    STATE_SELECTION=[('draft','Processing'), #Meaning Inputting data
                     ('approved','Approved'), #User Already Approved Adv., Received Money
                     ('waiting_for_complete','Reimbursed'),
                     ('cash_received','Cash Received'),
                     ('done','Completed'),
                     ('revising','Revising'),
                     ('cancel','Adv. Cancelled')]
    
    STATE_SELECTION_CASH = [('draft','Processing'), #Meaning Inputting data                     
                     ('cash_received','Cash Received'),
                     ('done','Completed'),
                     ('cancel','Cash Cancelled')]
    _columns={
                #String Fields
                'active': fields.boolean('Active'),
                'name': fields.char('Advance No.',track_visibility='onchange', size=16, required=True, select=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]}),
                'description':fields.text('Notes'),
                "location":fields.selection([('hanoi','Ha Noi Office'),('hcm','Ho Chi Minh Office'),('haiphong','Hai Phong Office')],'Location',select=1),
                #Date Fields
                'date':fields.date('Adv. Date', required=True, states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]}),
                
                'date_received_money':fields.date('Received Money',states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},help='Date of staff received money'),
                'date_of_received_reimbursement':fields.date('Received Reimbursement', states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},help='Date of Received Reimbursement Document from staff'),
                'date_of_settlement':fields.date('Settlement', states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]}),
                'date_acc_recv_doc':fields.date('Accounting Received Request Adv.',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},help='Date of Accounting dept. received documents (Advanced)'),
                'date_acc_recv_cashbook':fields.date('Accounting Received Cash Book',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]},help='Date of Accounting dept. received documents (Cash Book)'),
            #Amount Area
                
                #'exrate':fields.function(_get_exrate,help='Exchange rate from currency to company currency',
                #                         method=True,string="Ex.Rate",type='float',digits_compute=dp.get_precision('Amount')),

                #Number Amount
                'reimbursement_amount':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'), string='Reimbursement Amount',type='float', method=True, multi="kderp_advance_total",
                                                                store={
                                                                        'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','state'], 10),
                                                                        'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, None, 10),
                                                                       }),

                #'vourcher_total_amount':fields.float("voucher_"),
                
                #Function Fields
                'request_amount':fields.function(_amount_all, digits_compute= dp.get_precision('Amount'), string='Request Amount',type='float', method=True, multi="kderp_advance_total",
                                                store={
                                                        'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','state'], 10),
                                                        'kderp.advance.payment.line': (_get_adv_from_detail, None, 10),
                                                       }),
              
                'cash_return':fields.function(_amount_all,type='float',string='Cash Return',method=True,
                                              digits_compute= dp.get_precision('Amount'),multi="kderp_advance_total",
                                                store={
                                                        'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['date','currency_id','state'], 10),
                                                        'kderp.advance.payment.line': (_get_adv_from_detail, None, 10),
                                                        'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, None, 10),
                                                       }),
                'cash_payment':fields.function(_amount_all,type='float',string='Cash Payment',method=True,
                                              digits_compute= dp.get_precision('Amount'),multi="kderp_advance_total",
                                                store={
                                                        'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['date','currency_id','state'], 10),
                                                        'kderp.advance.payment.line': (_get_adv_from_detail, None, 10),
                                                        'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, None, 10),
                                                       }),
                'balance':fields.function(_amount_all,type='float',string='Balance',method=True,
                                              digits_compute= dp.get_precision('Amount'),multi="kderp_advance_total",
                                                store={
                                                        'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['date','currency_id','state'], 10),
                                                        'kderp.advance.payment.line': (_get_adv_from_detail, None, 10),
                                                        'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, None, 10),
                                                       }),
              
                'request_amount_to_word_vn':fields.function(_amount_to_word,string='Amount to Word',method=True,type='char',size=1000,multi="_amount_to_word",
                                                          store={
                                                                'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','state'], 15),
                                                                'kderp.advance.payment.line': (_get_adv_from_detail, None, 15),
                                                               }),
                'request_amount_to_word_en':fields.function(_amount_to_word,string='Amount to Word',method=True,type='char',size=1000,multi="_amount_to_word",
                                                          store={
                                                                'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','state'], 15),
                                                                'kderp.advance.payment.line': (_get_adv_from_detail, None, 15),
                                                               }),
              
                'total_voucher_amount_to_word_vn':fields.function(_voucher_amount_to_word,string='Amount to Word',method=True,type='char',size=1000,multi="_vourcher_amount_to_word",
                                                          store={
                                                                'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','state'], 15),
                                                                'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, None, 15)
                                                               }),
                'total_voucher_amount_to_word_en':fields.function(_voucher_amount_to_word,string='Amount to Word',method=True,type='char',size=1000,multi="_vourcher_amount_to_word",
                                                          store={
                                                                'kderp.advance.payment': (lambda self, cr, uid, ids, c={}: ids, ['currency_id','state'], 15),
                                                                'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, None, 15),
                                                               }),
                #Relation Fields
                'advance_buying':fields.selection([('material','Material'),('others','Others'),('cash','Cash')],'Type',required=True),
                'type_cash':fields.selection([('payment','Payment'),('receive','Receive')],'Cash type'),
                
                'user_id':fields.many2one('hr.employee','User',states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},ondelete="restrict"),
                'user_input':fields.many2one('hr.employee','Input User',states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},ondelete="restrict",readonly=True),
                
                'advance_line': fields.one2many('kderp.advance.payment.line', 'advance_id', 'Expense Details',states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},track_visibility='onchange'),
                'reimbursement_line': fields.one2many('kderp.advance.payment.reimbursement.line', 'advance_id', 'Reimbursement Details',states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},track_visibility='onchange'),
                
                'cash_line': fields.one2many('kderp.advance.payment.reimbursement.line', 'advance_id', 'Cash Details',states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},track_visibility='onchange'),
                
                'state':fields.selection(STATE_SELECTION,'Adv. Status',readonly=True,select=1),
                'state_cash':fields.function(_get_state,selection=STATE_SELECTION_CASH,
                                            type='selection',method=True,string='State',
                                             store={
                                                    'kderp.advance.payment':(lambda self, cr, uid, ids, c={}: ids, ['state'], 50),
                                                    }),                                
                               
                               
                'account_analytic_id':fields.many2one('account.analytic.account','Job',ondelete="restrict",
                                                      states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]}),
                'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True, states={'draft':[('readonly',False)]},ondelete="restrict"),
                'currency_id': fields.many2one("res.currency", string="Currency", required=True,states={'done':[('readonly',True)], 'cancel':[('readonly',True)],'cash_received':[('readonly',True)],'waiting_for_complete':[('readonly',True)]},ondelete="restrict"),
                
                'purchase_ids':fields.one2many('purchase.order', 'advance_payment_id', 'Purchase', domain=[('state','not in',('draft','cancel'))],readonly=True),
                'other_expense_ids':fields.one2many('kderp.other.expense', 'advance_payment_id', 'Other Expense', domain=[('state','not in',('draft','cancel'))],readonly=True),
                
                'outstanding':fields.function(_get_outstanding,type='boolean',string='Outstanding',method=True,
                                              store={
                                                     'kderp.advance.payment': (_get_adv_from_adv, ['state','user_id'], 10),
                                                     }),
              
                'payment_voucher_no':fields.char('Payment Voucher No.',size=16,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'receive_voucher_no':fields.char('Recv. Voucher No.',size=16,states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                
                'voucher_no_from_rbl':fields.function(_get_voucher_from_line,method=True,type='char',size=256,string='Voucher Nos',
                                                      store={'kderp.advance.payment.reimbursement.line': (_get_adv_from_reimbursement_detail, ['voucher_no'], 15),})
                #'cash_period_id':fields.function(_get_cash_period,type='many2one',relation='kderp.cash.period',string='Cash Period')
                                
              }
    _defaults={
               'active': True,
               'user_id':lambda *x:False,
               'user_input':lambda self, cr, uid, context:self.pool.get('hr.employee').search(cr, uid,[('user_id','=',uid)])[0] if self.pool.get('hr.employee').search(cr, uid,[('user_id','=',uid)]) else False, 
               'currency_id':lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id,
               'location':lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).location_user,
               'date': lambda *a: time.strftime('%Y-%m-%d'),
               'account_analytic_id':_get_job,
               'state':lambda *x: 'draft',
               'state_cash':lambda *x: 'draft',
               #'reimbursement_amount':lambda *x:0.0,
              # 'vourcher_total_amount':lambda *x:0.0,
               'request_amount':lambda *x:0.0,
               'cash_payment':lambda *x:0.0,
               'cash_return':lambda *x:0.0,
               'balance':lambda *x:0.0,
               'type_cash':lambda *x:'payment',
               'advance_buying':lambda *x:'others'
               }
    _sql_constraints = [
        ('advance_unique_no', 'unique(name)', 'Advance Number must be unique !'),
        ('advance_number_error_mask', "CHECK (name ilike 'AD___-____-%%' or name ilike 'C___-____-%%')",  'KDERP Error: The Advance number must like ADH13-1001-XXXX, CH13-1001-XXXX !'),
        ]

    #Inherit Default ORM
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'name':self.new_code(cr, uid, 0, self.browse(cr, uid, id,context).user_id.id,False,self.browse(cr, uid, id,context).advance_buying)['value']['name']
        })
        return super(kderp_advance_payment, self).copy(cr, uid, id, default, context)

    #Function to Workflow
    def wkf_action_open_for_revising(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'revising'})
        return True
    
    def wkf_action_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'})
        return True
    
    def wkf_action_cancel_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for adv_id in ids:
            wf_service.trg_create(uid, 'kderp.advance.payment', adv_id, cr)
        return True
    
    def wkf_action_processing_approved(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        todo = []
        period_obj = self.pool.get('account.period')
        for adv in self.browse(cr, uid, ids, context=context):
            val={}
            if not adv.advance_line:
                raise osv.except_osv('Error!','Please input detail of Advance Payment')

            if not adv.date_received_money:
                val['date_received_money']=time.strftime('%Y-%m-%d')
                
            period_id = adv.period_id and adv.period_id.id or False
            if not period_id:
                period_ids = period_obj.find(cr, uid, adv.date, context)
                period_id = period_ids and period_ids[0] or False
            val.update({'state' : 'approved', 'period_id':period_id})
            self.write(cr, uid, [adv.id], val)
        return True
    
    def wkf_action_approved_wfc(self, cr, uid, ids, context=None):
        if not context:
            context = {}

        for adv in self.browse(cr, uid, ids, context=context):
            val={}
            if not adv.date_of_received_reimbursement and adv.advance_buying<>'cash':
                val['date_of_received_reimbursement']=time.strftime('%Y-%m-%d')

            val.update({'state':'waiting_for_complete'})
            self.write(cr, uid, [adv.id], val)
        return True
    
    def wkf_action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    #Action For Process
    def wkf_action_submitting(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for adv_id in ids:
            wf_service.trg_validate(uid, 'kderp.advance.payment', id, 'btn_draft_to_processing', cr)
        return True
    
    def wkf_action_processing(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for adv_id in ids:
            wf_service.trg_validate(uid, 'kderp.advance.payment', id, 'btn_submitting_to_processing', cr)
        return True
    
    def wkf_action_approve(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for adv_id in ids:
            wf_service.trg_validate(uid, 'kderp.advance.payment', id, 'btn_processing_to_approved', cr)
        return True
    
    def wkf_action_done(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for adv_id in ids:
            wf_service.trg_validate(uid, 'kderp.advance.payment', id, 'btn_approved_done', cr)
        return True
    
    def pr_wkf_action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for adv_id in ids:
            wf_service.trg_validate(uid, 'kderp.advance.payment', id, 'btn_cancel', cr)
        return True
        
    def get_adv_ids(self, cr, uid, ids, *args):
        return ids
    
    def check_done(self, cr, uid, ids, *args):
        res=True
        write_done_ids=[]
                
        for adv in self.browse(cr, uid, ids, context={}):
            if adv.state=='waiting_for_complete' and adv.date_acc_recv_cashbook and adv.advance_buying!='cash':
                write_done_ids.append(adv.id)
            else:
                res = False
        if write_done_ids:
            self.write(cr, uid, write_done_ids,{'state':'done'})
        return res
kderp_advance_payment()
  
class kderp_advance_payment_line(osv.osv):
    _name='kderp.advance.payment.line'    
    _description='Customize Detail of Advance Payment for Kinden'

    _columns={
                'name':fields.char('Description',size=256,required=True),
                'amount':fields.float('Amount',digits_compute=dp.get_precision('Amount'),required=True),
                'remarks':fields.char('Remarks',size=128),
                'advance_id':fields.many2one('kderp.advance.payment','Advance',required=True,ondelete='cascade')
              }
kderp_advance_payment_line()

class kderp_advance_payment_reimbursement_line(osv.osv):
    _name='kderp.advance.payment.reimbursement.line'    
    _description='Detail of Reimbursement for Advance Payment Kinden'

    def create(self, cr, uid, vals, context=None):
        new_radv_id=super(kderp_advance_payment_reimbursement_line, self).create(cr, uid, vals, context=context)
        kcp_obj=self.pool.get('kderp.cash.period')
        kcp_obj.write(cr, uid, kcp_obj.find(cr, uid, vals['date']), {}, context)
        return new_radv_id
         
    def write(self, cr, uid, ids, vals, context=None):
        kcp_ids=[]
        kcp_obj=self.pool.get('kderp.cash.period')
        if 'amount' in vals:#'date' in vals or            
#             if vals.get('date',False):
#                 kcp_ids.extend(kcp_obj.find(cr, uid, vals['date'], context))                            
#             for kapl in self.read(cr, uid, ids, ['date']):
#                 kcp_ids.extend(kcp_obj.find(cr, uid, kapl['date'], context))
            for kaprl_obj in self.browse(cr, uid, ids):
                if kaprl_obj.advance_id.date_of_received_reimbursement:
                    kcp_ids.extend(kcp_obj.find(cr, uid, kaprl_obj.advance_id.date_of_received_reimbursement, context))
                if kaprl_obj.advance_id.date_received_money:
                    kcp_ids.extend(kcp_obj.find(cr, uid, kaprl_obj.advance_id.date_received_money, context))
                    
        new_obj = super(kderp_advance_payment_reimbursement_line, self).write(cr, uid, ids, vals, context=context)
        
        if len(list(set(kcp_ids)))>0:
            kcp_obj.write(cr, uid, list(set(kcp_ids)), {}, context)                
        return new_obj
    
    def _amount_to_word(self, cr, uid, ids, name, args, context={}):
        res = {}
        for x in self.browse(cr,uid,ids, context=context):
            request_amount=x.amount if x.amount>=0 else 0
            if x.advance_id.currency_id.name=='USD':
                amount_to_word_vn = amount_to_text(request_amount,'vn',u" \u0111\xf4la",decimal='cents').capitalize()
                amount_to_word_en = amount_to_text(request_amount,'en'," dollar").capitalize()
            elif x.advance_id.currency_id.name=='VND':
                amount_to_word_vn = amount_to_text(request_amount,'vn', u' \u0111\u1ed3ng').capitalize()  # + x.currency_id.name
                amount_to_word_en = amount_to_text(request_amount,"en","dongs").capitalize()
            else:
                amount_to_word_vn =amount_to_text(request_amount,'vn'," " + x.advance_id.currency_id.name).capitalize()
                amount_to_word_en =amount_to_text(request_amount,'en'," "+ x.advance_id.currency_id.name).capitalize() 
            res[x.id] = {'amount_to_word_vn':amount_to_word_vn,
                         'amount_to_word_en':amount_to_word_en}
        return res
    
    def get_new_voucher_code(self, cr, uid, ids, date, voucher_no, currency,type_cash='payment'):
        result={}
        result=self.pool.get('kderp.advance.payment').get_new_voucher(cr, uid, ids, date, voucher_no, False, False,  currency, 'typeCash',type_cash)
        if 'payment_voucher_no' in result['value']:
            result['value'].update({'voucher_no':result['value'].pop('payment_voucher_no')})
        return result
    
    def _get_adv_from_rbl_line(self, cr, uid, ids, context=None):
        res = []
        for adv in self.pool.get('kderp.advance.payment').browse(cr, uid, ids, context=context):
            for rbl in adv.reimbursement_line:
                res.append(rbl.id)
            for rbl in adv.cash_line:
                res.append(rbl.id)
        return list(set(res))

    _order= "date"
    _order= "voucher_no"
    _columns={
                'date':fields.date('Date',required=True),
                'supplier_id':fields.many2one('res.partner','Payer',ondelete='restrict'),
                'user_id':fields.many2one('hr.employee','User',ondelete='restrict'),
                'name':fields.char('Description',size=256,required=True),
                'amount':fields.float('Amount',digits_compute=dp.get_precision('Amount'),required=True),
                
                'amount_to_word_vn':fields.function(_amount_to_word,string='Amount to Word',method=True,type='char',size=1000,multi="_amount_to_word_rbl",
                                                          store={
                                                                'kderp.advance.payment.reimbursement.line': (lambda self, cr, uid, ids, c={}: ids, ['amount'], 15),                                                                
                                                                'kderp.advance.payment': (_get_adv_from_rbl_line,['currency_id'], 15)
                                                               }),
                'amount_to_word_en':fields.function(_amount_to_word,string='Amount to Word',method=True,type='char',size=1000,multi="_amount_to_word_rbl",
                                                          store={
                                                                'kderp.advance.payment.reimbursement.line': (lambda self, cr, uid, ids, c={}: ids, ['amount'], 15),
                                                                'kderp.advance.payment': (_get_adv_from_rbl_line,['currency_id'], 15)
                                                               }),              
                                
                'advance_id':fields.many2one('kderp.advance.payment','Advance',required=True,ondelete='cascade'),
                'voucher_no':fields.char('Voucher No.',size=16),
                'other_user':fields.char('Other User',size=32),
              }
    _defaults = {
                 'user_id': lambda obj,cr,uid,context:context.get('user_id',False)
                 }
kderp_advance_payment_reimbursement_line()