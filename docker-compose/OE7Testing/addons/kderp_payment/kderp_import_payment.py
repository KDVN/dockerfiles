# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
import time

import openerp.addons.decimal_precision as dp

class kderp_import_payment(osv.osv):
    _name = "kderp.import.payment"
    _description = "KDERP Import Payment"
    _order='date desc'
    
    def kpi_submit(self, cr, uid, ids, context={}):   
        #Update Supplier Payment Expense     
        fields_list_need="total,ksp.currency_id,ksp.exrate,kpil.date"
        cr.execute("""Select 
                            ksp.id as ksp_id,
                            ksp.name as payment_number,
                            kpil.id as kpil_id,
                            %s
                      from 
                          kderp_import_payment_line kpil
                      left join
                          kderp_supplier_payment_expense ksp on upper(payment_number)=upper(ksp.name)
                      where
                            ksp.state='completed' and payment_import_id in (%s) and kpil.state='draft'"""  % (fields_list_need,",".join(map(str,ids))))
        
        list_update_error=[]        
        kpe_obj=self.pool.get('kderp.supplier.payment.expense.pay')
        kp_obj=self.pool.get('kderp.supplier.payment.pay')
        kpil_obj=self.pool.get('kderp.import.payment.line')
       
        for ksp_id,payment_no,kpil_id,amount,currency,exrate,date in cr.fetchall():
            try:
                kpe_obj.create(cr, uid, {'supplier_payment_expense_id':ksp_id,
                                          'amount':amount,
                                          'currency_id':currency,
                                          'exrate':exrate,
                                          'date':date},
                                          context)
                kpil_obj.write(cr, uid, [kpil_id],{'state':'done'})
                cr.commit()
            except ValueError, e:
                list_update_error.append({payment_no:unicode(e)})
                cr.rollback()

       #Update Supplier Payment 
        cr.execute("""Select 
                            ksp.id as ksp_id,
                            ksp.name as payment_number,
                            kpil.id as kpil_id,
                            %s 
                      from 
                          kderp_import_payment_line kpil
                      left join
                          kderp_supplier_payment ksp on upper(payment_number)=upper(ksp.name)
                      where
                          ksp.state='completed' and 
                          payment_import_id in (%s) and 
                          kpil.state='draft'"""  % (fields_list_need,",".join(map(str,ids))))
         
        for ksp_id,payment_no,kpil_id,amount,currency,exrate,date in cr.fetchall():
            try:
                kp_obj.create(cr, uid, {'supplier_payment_id':ksp_id,
                                          'amount':amount,
                                          'currency_id':currency,
                                          'exrate':exrate,
                                          'date':date},
                                          context)
                kpil_obj.write(cr, uid, [kpil_id],{'state':'done'})
                cr.commit()
            except ValueError, e:
                cr.rollback()
                list_update_error.append({payment_no:unicode(e)})
                
        if list_update_error:
            raise osv.except_osv("KDERP Notification",list_update_error)
        else:
            kip_ids=",".join(map(str,ids))
            cr.execute("Select payment_import_id id from kderp_import_payment_line where payment_import_id in (%s) and state='draft'" % (kip_ids))
            list_error=[]
            for new_id in cr.fetchall():
                list_error.append(new_id[0])
            for id in ids:
                if id not in list_error:
                    self.write(cr, uid, [id], {'state':'done'})
        return True        
    
    _columns={
                'date':fields.date('Date', required=True, states={'done':[('readonly',True)]}, help="Date of Accounting Import Payment to Supplier to ERP"),
                'name':fields.char('Code Import',size=32,required=True,select=True,states={'done':[('readonly',True)]}),
                'description':fields.char('Desc.',size=128,states={'done':[('readonly',True)]}),
                'import_line':fields.one2many('kderp.import.payment.line','payment_import_id','Details',states={'done':[('readonly',True)]}),
                'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True,select=True)               
              }
    _sql_constraints = [
                        ('supplier_payment_import_unique',"unique(name)","KDERP Error: The Code Import must be unique !")
                        ]
    _defaults = {
        'state': 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'name':lambda *a: time.strftime('AISP-%Y%b%d.%H%M')
        }
    
    def load(self, cr, uid, fields, data, context=None):
    #def import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
        try:
            payment_id_pos = fields.index('import_line/payment_number')
        except:
            payment_id_pos = -1
        
        data=list(set(data))
        
        payment_no_list =[]
        payment_expense_no_list =[]
        if payment_id_pos>=0:
            for pos in range(len(data)):
                if data[pos][payment_id_pos].upper().find('IN')>=0:
                    payment_no_list.append(str(data[pos][payment_id_pos]))
                elif data[pos][payment_id_pos].upper().find('EN')>=0 or data[pos][payment_id_pos].upper().find('GN')>=0:
                    payment_expense_no_list.append(str(data[pos][payment_id_pos]))
            payment_nos =str(payment_no_list if payment_no_list else "['false']" ).replace("[","(").replace("]",")")
            payment_expense_nos=str(payment_expense_no_list if payment_expense_no_list else "['false']").replace("[","(").replace("]",")")
#             raise osv.except_osv("KDVN Error",new_data)
            cr.execute("""Select 
                            name 
                          from 
                              kderp_supplier_payment krop 
                          where 
                              name in %s and state!='completed'
                          Union
                          Select 
                            name 
                          from 
                              kderp_supplier_payment_expense krop 
                          where 
                              name in %s and state!='completed'""" % (payment_nos ,payment_expense_nos))
            if cr.rowcount>0:
                list1 =[]
                for pn in cr.fetchall():
                    list1.append(str(pn[0]))
                raise osv.except_osv("KDVN Error","State of payment must be BOD Approved !\n%s" % str(list1))
             
        return super(kderp_import_payment, self).load( cr, uid, fields, data, context)
      
kderp_import_payment()

class kderp_import_payment_line(osv.osv):
    _name = "kderp.import.payment.line"
    _description = "KDERP Import Payment Line"
    _rec_name='payment_number'
    _order='state desc,payment_number'
    
    _columns={
                'date':fields.date('Date', select=True, required=True,help="Effective date for accounting entries"),
                'currency_id': fields.many2one('res.currency', 'Currency'),
                'amount': fields.float("Amount", digits_compute=dp.get_precision('Account')),
                'exrate': fields.float("Ex.Rate",digits_compute=dp.get_precision('Amount')),
                'move_id': fields.many2one('account.move', 'Detail',select=1,ondelete='restrict'),
                'writeoff':fields.boolean('Write-Off',),
                'bank_id':fields.many2one('res.bank','Bank',select=True,),
                'payment_number':fields.char('Payment No.',size=16,required=True),
                'payment_import_id':fields.many2one('kderp.import.payment','Payment Import',required=True),
                'state':fields.selection([('draft','Draft'),('done','Done')],'State',readonly=True,select=True)
              }
    _defaults = {
        'state': 'draft'
        }
    _sql_constraints = [
                        ('supplier_payment_import_line_unique',"unique(payment_number)","KDERP Error: The Supplier Payment must be unique !")
                        ]
kderp_import_payment_line()