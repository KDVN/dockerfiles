# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
try:
    from kderp_base.amount_to_text import *
except:
    pass

class kderp_cashonhand_report_wizard(osv.osv_memory):
    _name = 'kderp.cashonhand.report'
    _description = 'KDERP Cash On Hand Report Wizard'
    _rec_name = 'date_start'    
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        if type(ids).__name__!='list':
            ids=[ids]
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        from time import strptime
        from datetime import datetime
        for elmt in self.browse(cr, uid, ids, context=context):
            from_date=datetime(*(strptime(elmt.date_start,("%Y-%m-%d"))[0:6])).strftime("%d-%b-%Y")
            to_date=datetime(*(strptime(elmt.date_stop,("%Y-%m-%d"))[0:6])).strftime("%d-%b-%Y")
            res.append((elmt.id,"Cash on Hand report %s ~ %s" % (from_date,to_date)))
        return res
    
    def onchange_date(self, cr, uid, ids, date_start,date_stop, one_year, currency_id, location,context={}):
        result={}
        if date_start and date_stop:                
            cr.execute("""Select 
                            kdca.id
                        from 
                            kderp_detail_cash_advance kdca
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            date between '%s' and '%s' and currency_id=%s and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end""" % (date_start,date_stop,currency_id,uid,location,location))
            detail_ids = [x[0] for x in cr.fetchall()]
            result={'detail_ids':detail_ids}            
        return {'value':result}
    
    def on_period(self, cr, uid, ids, period_id,detail_ids,context={}):
        result={'detail_ids':detail_ids}
        if period_id:
            dates = self.pool.get('kderp.cash.period').read(cr, uid, period_id,['date_start','date_stop'],context)
            result.update({'date_start':dates['date_start'],
                    'date_stop':dates['date_stop']})        
        return {'value':result}
    
    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        periods = self.pool.get('kderp.cash.period').find(cr, uid, context=ctx,prev=True)
        if periods:
            return periods[0]
        return False
    
    def _get_details_defaults(self, cr, uid, context=None):
        res=[]
        ctx = dict(context or {}, account_period_prefer_normal=True)
        periods = self.pool.get('kderp.cash.period').find(cr, uid, context=ctx,prev=True)
        if periods:
            currency_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
            dates = self.pool.get('kderp.cash.period').read(cr, uid, periods[0],['date_start','date_stop'],context)
            date_start=dates['date_start']
            date_stop=dates['date_stop']
            location= self.pool.get('res.users').browse(cr, uid, uid).location_user
            cr.execute("""Select
                            distinct
                            kdca.id
                        from 
                            kderp_detail_cash_advance kdca
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end
                            and
                            date between '%s' and '%s' and currency_id=%s and ru.id=%s""" % (location,location,date_start,date_stop,currency_id,uid))
            for uid in cr.fetchall():
                res.append(uid[0])
        return res
    
    def compute(self, cr, uid, ids, context=None):
        return {
                'tag': 'reload',
                'type': 'ir.actions.act_window_close' 
                }
        
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': ids}
        datas['model'] = 'kderp.cashonhand.report'
        datas['title'] = 'Cash on Hand Report'
        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'kderp.cash.on.hand',
            'datas': datas}
        
    def action_open_detail(self, cr, uid, ids, context=None):        
        data = self.read(cr, uid, ids, ['date_start','date_stop'],context=context)[0]
        from time import strptime
        from datetime import datetime
        
        from_date=datetime(*(strptime(data['date_start'],("%Y-%m-%d"))[0:6])).strftime("%d-%b-%Y")
        to_date=datetime(*(strptime(data['date_stop'],("%Y-%m-%d"))[0:6])).strftime("%d-%b-%Y")
            
        return {
            'domain': "[('date','>=','%s'),('date','<=','%s')]" % (data['date_start'],data['date_stop']),
            'name': 'Cash on Hand %s ~ %s' % (from_date,to_date),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'kderp.detail.cash.advance',
            'type': 'ir.actions.act_window'
            }
    
    def _get_detail_list(self, cr, uid, ids, name, args, context={}):
        res={}
        for obj in self.browse(cr, uid, ids, context):
            date_start=obj.date_start
            date_stop=obj.date_stop
            location=obj.location
            res[obj.id]=[]
            
            cr.execute("""Select
                            distinct
                            kdca.id,
                            date,sort,voucher_no,staffno
                        from 
                            kderp_detail_cash_advance kdca
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            date between '%s' and '%s' and currency_id=%s                            
                            and  
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end
                            and 
                                ru.id=%s
                        order by
                            date,sort,voucher_no,staffno
                            """ % (date_start,date_stop,obj.currency_id.id,location,location,uid))
            for kdca_id,d,s,v,st in cr.fetchall():
                res[obj.id].append(kdca_id)
            res[obj.id]={'detail_ids':res[obj.id]}
        return res            
            
    def _get_total_in_list(self, cr, uid, ids, name, args, context={}):
        res={}
        for obj in self.browse(cr, uid, ids, context):
            date_start=obj.date_start
            date_stop=obj.date_stop
            location=obj.location
            res[obj.id]={'opening_balance':0,
                         'balance':0,
                         'closing_balance':0}
            if obj.one_year:
                new_condition="kdca.date>='%s' and kdca.date<'%s'" % (date_start[:4]+"-01-01",date_start)
            else:
                new_condition="kdca.date<'%s'" % date_start
                
            cr.execute("""
                        Select 
                            sum(coalesce(debit,0)-coalesce(credit,0)) as balance,
                            sum(coalesce(debit,0)-coalesce(credit,0))+coalesce(opening_balance,0) as closing_balance,
                            coalesce(opening_balance,0) as opening_balance
                        from 
                            kderp_detail_cash_advance kdca
                        left join
                            (Select 
                                sum(coalesce(debit,0)-coalesce(credit,0)) as opening_balance
                            from 
                                kderp_detail_cash_advance kdca
                            left join
                                res_currency rc on currency_id=rc.id
                            left join
                                res_users ru on substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                            where
                                %s and currency_id=%s and ru.id=%s) vwopenning on 1=1
                        left join
                            res_currency rc on currency_id=rc.id
                        left join
                            res_users ru on substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            kdca.date between '%s' and '%s' and currency_id=%s and ru.id=%s and
                            substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end
                        group by
                            opening_balance""" % (new_condition,obj.currency_id.id,uid,date_start,date_stop,obj.currency_id.id,uid,location,location))
            result=cr.dictfetchone()
            if result:
                res[obj.id]=result                         
        return res
      
    _columns = {
                'period_id':fields.many2one('kderp.cash.period','Months'),
                'location':fields.selection([('hanoi','Ha Noi'),('haiphong','Hai Phong')],'Location',required=True),
                'currency_id':fields.many2one('res.currency','Currency',domain=[('name','in',('VND','USD'))],required=1),
                'date_start':fields.date('Start Date',required=1),
                'date_stop':fields.date('Stop Date',required=1),
                'one_year':fields.boolean('One Year',help='Select current year, Opening Balance calculate base on year of date start.'),
                'detail_ids':fields.function(_get_detail_list,obj='kderp.detail.cash.advance',type='one2many',string='Details',method=True,multi="_Get_detail"),
                
                'opening_balance':fields.function(_get_total_in_list,type='float',string='Opening Balance',method=True,multi='_get_balance'),
                'closing_balance':fields.function(_get_total_in_list,type='float',string='Closing Balance',method=True,multi='_get_balance'),
                'balance':fields.function(_get_total_in_list,type='float',string='Balance',method=True,multi='_get_balance'),
                }
    _defaults = {
                'one_year':True,
                'period_id':_get_period,
                'detail_ids':_get_details_defaults,
                'currency_id':lambda self, cr, uid, context={}: self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id,
                'location':lambda self, cr, uid, context={}: self.pool.get('res.users').browse(cr, uid, uid).location_user
                }
kderp_cashonhand_report_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
