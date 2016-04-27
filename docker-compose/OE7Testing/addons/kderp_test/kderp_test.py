import re
import time
import datetime
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_round, float_is_zero, float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
class kderp_test(osv.osv):
    _name = "kderp.test"
    _description = "Test"
  
    def _total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for total in self.browse(cr, uid, ids, context=context):
            res[total.id] = {
                'total_1': 0.0,
                'total_2': 0.0,
                'number_1':0.0,
                'number_2':0.0
                }
            val = val1 = 0.0
            val = total.number_1
            val1= total.number_2
            res[total.id]['number_1'] =  val
            res[total.id]['number_2'] =  val1
            res[total.id]['total_1'] = res[total.id]['number_1'] + res[total.id]['number_2']
        return res 
    def _note(self,cr,uid,ids,field_name,arg,context=None):
        res={}
        for note in self.browse(cr,uid,ids,context=context):
            res[note.id]={
                       'number_1':0.0,}
            val=0.0
            res[note.id]['number_1'] =  val
            if (res[note.id]['number_1'] % 2) ==1:
                res[note.id]['note']='Number 1 la so Le'
        return res
    def onchange_note(self, cr, uid, ids,number_1):#Auto fill location when change Owner
        if(number_1%2)==1:
            return {'value':{'note':'Number 1 So Le'}}
        else:
            return {'value':{'note':'Number 1 so Chan'}}
              
    def onchange_note2(self,cr,uid,ids,number_2):
        if (number_2%number_2)==0and((number_2/1)==number_2):
            return {'value':{'note2':'Number 2 La so nguyen to'}}
        else:
            return {'value':{'note2':'Number 2 khong la so nguyen to'}}
   
    def _onchange_date(self, cr, uid, ids,rop_date_str):
        if rop_date_str:
            from datetime import datetime as ldatetime
            rop_date = ldatetime.strptime(rop_date_str, '%Y-%m-%d')           
            m = rop_date.month
            d = rop_date.day
            y = rop_date.year
            if m==12 :
                if (d>25):
                    m = 2
                    y = y + 1
                    d = 10                                
                elif (d<11):
                    m = 1
                    y = y + 1
                    d = 10
                else:
                    m = 1
                    y = y + 1
                    d = 25                            
            elif m==11:
                if (d>25):
                    m = 1
                    y = y + 1
                    d = 10
                elif (d<11):
                    m= m +1
                    d = 10
                else:
                    m= m +1
                    d= 25
            else:
                if (d>25):
                    m = m + 2
                    d = 10
                elif (d<11):
                    m = m + 1
                    d = 10
                else:
                    m = m + 1
                    d = 25 
            due_date = datetime.date(y, m, d).strftime("%Y-%m-%d")
            #raise osv.except_osv(,due_date)
        else:
            due_date = False
        #raise osv.except_osv("E",{'value':{'due_date':due_date}})    
        return due_date
    _columns={
              
              'start_date':fields.date('Start Date'),
              'end_date':fields.date('End Date'),
              'number_1':fields.float('Number1'),
              'number_2':fields.float('Number2'),
              'total_1':fields.function(_total,multi='_get_total',
                                         method=True,string="Total",type='float',
                                         store={
                                                 'kderp.test': (lambda self, cr, uid, ids, c={}: ids, ['number_1','number_2'], 10),
                                               }),
              'total_2':fields.float('Number2'),
              'note':fields.char('Note.',size=16,),
              'note2':fields.char('Note',size=30),
              'list_code':fields.char('Code',size=20)
              
              
              }
    _defaults={
               }
    
kderp_test()

