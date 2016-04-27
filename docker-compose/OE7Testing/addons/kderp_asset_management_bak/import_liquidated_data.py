import time
from datetime import datetime
from openerp.osv.orm import Model
from openerp.osv import fields, osv
import re

class kderp_asset_import(Model):
    _name = 'kderp.asset.limport'
    _description='KDERP Import Liquidated'
    _order='name desc'
        
    _columns={
              'name':fields.date("Import Date", 
                                    states={'done':[('readonly',True)]}, required=True),              
              'remarks':fields.char('Remarks',size=256, 
                                    states={'done':[('readonly',True)]}),                                                               
                                                                
              'state':fields.selection((('draft','Draft'),('done','Completed')),'state',readonly=True),
              'detail_ids':fields.one2many('kderp.import.asset.detail','import_id','Details',states={'done':[('readonly',True)]}),                       
              }
    _defaults={
               'name':lambda *a: time.strftime('%Y-%m-%d'),
               'state':lambda *a: 'draft'
               }
    
    def load(self, cr, uid, fields, data, context=None):
    #def import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
        raise osv.except_osv("E","%s-%s" % (fields,data))
        try:
            payment_id_pos = fields.index('AssetCode')
        except:
            payment_id_pos = -1
        
        data=list(set(data))
        
        payment_no_list =[]
        payment_expense_no_list =[]
        if payment_id_pos>=0:
            for pos in range(len(data)):
                if data[pos][payment_id_pos].upper().find('IN')>=0:
                    payment_no_list.append(str(data[pos][payment_id_pos]))
                elif data[pos][payment_id_pos].upper().find('EN')>=0:
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
             
        return super(kderp_import_liquidated, self).load( cr, uid, fields, data, context)
      

class kderp_import_asset_detail(Model):
    _name = 'kderp.import.asset.detail'
    
    _columns={
              'import_id':fields.many2one('kderp.asset.limport','Import', required=True),
              'asset_id':fields.many2one('kderp.asset.management','Asset', required=True),
              'date':fields.date('Date', required=True),
              'remarks':fields.char('Remark',size=256)
              }
    