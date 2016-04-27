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

class kderp_advance_report_wizard(osv.osv_memory):
    _name = 'kderp.user.advance.report'
    _description = 'KDERP User Advance Report Wizard'
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
            res.append((elmt.id,"Advance Check report %s ~ %s" % (from_date,to_date)))
        return res
    
    def onchange_date(self, cr, uid, ids, date_start,date_stop, one_year, location, context={}):
        result={}
        if date_start and date_stop:
            if one_year:
                new_condition="date>='%s' and date<'%s'" % (date_start[:4]+"-01-01",date_start)
            else:
                new_condition="date<'%s'" % date_start
                
            cr.execute("""Select 
                            distinct
                            voa.user_id
                        from 
                            vwdetail_of_advance voa
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            date between '%s' and '%s' and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else '_' end end
                        Group by
                             voa.user_id
                        Union
                        Select 
                            user_id
                        from 
                            vwdetail_of_advance voa
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end    
                        where
                            %s  and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else '_' end end
                        group by
                            user_id
                        having
                             sum(coalesce(credit,0)-coalesce(debit,0))>0""" % (date_start,date_stop,uid,location,location,new_condition,uid,location,location))
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
            dates = self.pool.get('kderp.cash.period').read(cr, uid, periods[0],['date_start','date_stop'],context)
            date_start=dates['date_start']
            date_stop=dates['date_stop']
            location=self.pool.get('res.users').browse(cr, uid, uid).location_user
            new_condition="date>='%s' and date<'%s'" % (date_start[:4]+"-01-01",date_start)
                
            cr.execute("""Select 
                            voa.user_id
                        from 
                            vwdetail_of_advance voa
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end  
                        where
                            date between '%s' and '%s' and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else '_' end end
                        Group by
                             voa.user_id
                        Union
                        Select 
                            user_id
                        from 
                            vwdetail_of_advance voa
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end  
                        where
                            %s and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else '_' end end
                        group by
                            user_id
                        having
                             sum(coalesce(credit,0)-coalesce(debit,0))>0""" % (date_start,date_stop,uid,location,location,new_condition,uid,location,location))
            for uid in cr.fetchall():
                res.append(uid[0])
            res=list(set(res))
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
        datas['model'] = 'kderp.user.advance.report'
        datas['title'] = 'Account Check Report'        
        
        report_name='kderp.advance.check.report.xls' if self.browse(cr, uid, ids[0]).excel else 'kderp.advance.check.report'
         
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas}
        
    def action_open_detail(self, cr, uid, ids, context=None):        
        data = self.read(cr, uid, ids, ['date_start','date_stop'],context=context)[0]
        return {
            'domain': "[('date','>=','%s'),('date','<=','%s'),('type','in',('request_advance','return_advance'))]" % (data['date_start'],data['date_stop']),
            'name': 'Detail Of Advance',
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
            if obj.one_year:
                new_condition="date>='%s' and date<'%s'" % (date_start[:4]+"-01-01",date_start)
            else:
                new_condition="date<'%s'" % date_start
                
            cr.execute("""Select 
                            distinct
                            voa.user_id
                        from 
                            vwdetail_of_advance voa
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            date between '%s' and '%s' and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else '_' end end
                        Group by
                             voa.user_id
                        Union
                        Select 
                            user_id
                        from 
                            vwdetail_of_advance voa
                        left join
                            res_users ru on substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                        where
                            %s and ru.id=%s and
                            substring(name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else '_' end end
                        group by
                            user_id
                        having
                             sum(coalesce(credit,0)-coalesce(debit,0))>0""" % (date_start,date_stop,uid,location,location,new_condition,uid,location,location))
            for uid in cr.fetchall():
                res[obj.id].append(uid[0])
            res[obj.id]={'detail_ids':list(set(res[obj.id]))}                        
            return res            
            
    def _get_total_in_list(self, cr, uid, ids, name, args, context={}):
        res={}
        for obj in self.browse(cr, uid, ids, context):
            total_amount_vnd=0
            total_amount_usd=0
            
            for objl in obj.detail_ids:                          
                total_amount_vnd+=objl.opening_balance + objl.request_adv - objl.return_adv 
                total_amount_usd+=objl.opening_balance_usd + objl.request_adv_usd - objl.return_adv_usd
            
            nego_vnd=False
            if total_amount_vnd<0:
                nego_vnd = True
            
            nego_usd=False
            if total_amount_usd<0:
                nego_usd = True
            
            amount_in_word_vnd_vn = amount_to_text(abs(total_amount_vnd),'vn', u' \u0111\u1ed3ng').capitalize()
            amount_in_word_vnd_en = amount_to_text(abs(total_amount_vnd),"en","dongs").capitalize()
            
            amount_in_word_usd_vn = amount_to_text(abs(total_amount_usd),'vn'," dollar").capitalize()
            amount_in_word_usd_en = amount_to_text(abs(total_amount_usd),'en'," dollar").capitalize()
            res[obj.id]={'total_amount_vnd':total_amount_vnd,
                         'amount_in_word_vnd_vn': ('(%s)' if nego_vnd else '%s')  % amount_in_word_vnd_vn,
                         'amount_in_word_vnd_en':('(%s)' if nego_vnd else '%s')  % amount_in_word_vnd_en,
                         
                         'total_amount_usd':total_amount_usd,
                         'amount_in_word_usd_vn':('(%s)' if nego_usd else '%s') % amount_in_word_usd_vn,
                         'amount_in_word_usd_en':('(%s)' if nego_usd else '%s') % amount_in_word_usd_en                         
                         }            
        return res
      
    _columns = {
                'location':fields.selection([('hanoi','Ha Noi'),('haiphong','Hai Phong')],'Location',required=True),
                'period_id':fields.many2one('kderp.cash.period','Months'),
                'date_start':fields.date('Start Date',required=1),
                'date_stop':fields.date('Stop Date',required=1),
                'one_year':fields.boolean('One Year',help='Select current year, Opening Balance calculate base on year of date start.'),
                'excel':fields.boolean("Excel File?"),
                
                'detail_ids':fields.function(_get_detail_list,obj='kderp.advance.check.detail.user.report',type='one2many',string='Details',method=True,multi="_Get_detail"),
                
                'total_amount_vnd':fields.function(_get_total_in_list,type='float',string='In VND',method=True,multi="_Get_total"),
                'amount_in_word_vnd_vn':fields.function(_get_total_in_list,type='char',string='In Words VND VN',method=True,multi="_Get_total"),
                'amount_in_word_vnd_en':fields.function(_get_total_in_list,type='char',string='In Words VND EN',method=True,multi="_Get_total"),
                
                'total_amount_usd':fields.function(_get_total_in_list,type='float',string='In USD',method=True,multi="_Get_total"),
                'amount_in_word_usd_vn':fields.function(_get_total_in_list,type='char',string='In Words USD VN',method=True,multi="_Get_total"),
                'amount_in_word_usd_en':fields.function(_get_total_in_list,type='char',string='In Words USD EN',method=True,multi="_Get_total"),
                }
    _defaults = {
                'excel':False,
                'one_year':True,
                'period_id':_get_period,
                'detail_ids':_get_details_defaults,
                'location':lambda self, cr, uid, context={}: self.pool.get('res.users').browse(cr, uid, uid).location_user
                }
kderp_advance_report_wizard()

class kderp_advance_check_detail_user_report(osv.osv):
    _name='kderp.advance.check.detail.user.report'
    _auto=False
    _rec_name='user_id'
    
    def _get_detail(self, cr, uid, ids, name, args, context={}):
        res={}
        if not context:
            context={}
        #raise osv.except_osv("E",context)
        for id in ids:
            res[id]={'opening_balance':0,'request_adv':0,'return_adv':0,
                     'opening_balance_usd':0,'request_adv_usd':0,'return_adv_usd':0}
        date_start=context.get('date_start',False)
        date_stop=context.get('date_stop',False)
        one_year=context.get('one_year',False)
        location=context.get('location',False)
        
        if not date_start and context.get('active_id',False):          
            main_id=context.get('active_id',0)
            main_obj=self.pool.get('kderp.user.advance.report').browse(cr, uid, main_id, context)
            date_start=main_obj.date_start
            date_stop=main_obj.date_stop
            one_year=main_obj.one_year
            location=main_obj.location
                
        if not date_start:
            return res
        else:
            if one_year:
                new_condition="voa.date>='%s' and voa.date<'%s'" % (date_start[:4]+"-01-01",date_start)
            else:
                new_condition="voa.date<'%s'" % date_start
                 
        cr.execute("""
                    Select 
                        user_id,
                        opening_balance as opening_balance,
                        sum(request_adv) as request_adv,
                        sum(return_adv) as return_adv,
                        opening_balance_usd as opening_balance_usd,
                        sum(request_adv_usd) as request_adv_usd,
                        sum(return_adv_usd) as return_adv_usd
                    from
                        (
                            Select 
                                voa.user_id,
                                coalesce(previous_balance,0) as opening_balance,
                                sum(case when rc.name='VND' then coalesce(credit,0) else 0 end) as request_adv,
                                sum(case when rc.name='VND' then coalesce(debit,0) else 0 end) as return_adv,
                                coalesce(previous_balance_usd,0) as opening_balance_usd,
                                sum(case when rc.name='USD' then coalesce(credit,0) else 0 end) as request_adv_usd,
                                sum(case when rc.name='USD' then coalesce(debit,0) else 0 end) as return_adv_usd
                            from 
                                vwdetail_of_advance voa
                            left join
                                 res_currency rc on currency_id=rc.id
                            left join
                                (Select 
                                    user_id,
                                    sum(case when rc.name='VND' then coalesce(credit,0) - coalesce(debit,0)  else 0 end) as previous_balance,
                                    sum(case when rc.name='USD' then coalesce(credit,0) - coalesce(debit,0)  else 0 end) as previous_balance_usd
                                from 
                                    vwdetail_of_advance voa
                                left join
                                    res_currency rc on currency_id=rc.id
                                left join
                                    res_users ru on substring(voa.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                                where
                                    %s and ru.id=%s and
                                    substring(voa.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end
                                group by
                                    user_id) vwtemp on voa.user_id=vwtemp.user_id
                            left join
                                res_users ru on substring(voa.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                            where
                                voa.date between '%s' and '%s' and ru.id=%s and
                                substring(voa.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end
                            Group by
                                 voa.user_id,
                                 previous_balance,
                                 previous_balance_usd
                            Union
                            Select 
                                    voa.user_id,
                                    sum(case when rc.name='VND' then coalesce(credit,0) - coalesce(debit,0)  else 0 end) as opening_balance,                                    
                                    0 as request_adv,                                    
                                    0 as return_adv,
                                    sum(case when rc.name='USD' then coalesce(credit,0) - coalesce(debit,0)  else 0 end) as opening_balance_usd,
                                    0 as request_adv_usd,                                    
                                    0 as return_adv_usd
                                from 
                                    vwdetail_of_advance voa
                                left join
                                    res_currency rc on currency_id=rc.id
                                left join
                                    res_users ru on substring(voa.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when location_user='haiphong' then 'P' else case when location_user='hanoi' then 'H' else '_' end end
                                where
                                    %s and ru.id=%s and
                                    substring(voa.name from (case when type='cash' then 2 else 3 end) for 1) ilike case when '%s'='haiphong' then 'P' else case when '%s'='hanoi' then 'H' else 'S' end end
                                Group by
                                     voa.user_id
                                having
                                     sum(coalesce(credit,0)-coalesce(debit,0))>0) vwcombine
                        group by user_id,opening_balance,opening_balance_usd""" % (new_condition,uid,location,location,date_start,date_stop,uid,location,location,new_condition,uid,location,location))
        for obj in cr.dictfetchall():
            res[obj.pop('user_id')]=obj                        
        return res
    
    _columns={
                'user_id':fields.many2one('hr.employee',"User",readonly=1),
                'opening_balance':fields.function(_get_detail,type='float',string='Opening VND',method=True,multi='_get_details'),
                'request_adv':fields.function(_get_detail,type='float',string='Request Adv. VND',method=True,multi='_get_details'),
                'return_adv':fields.function(_get_detail,type='float',string='Return Adv. VND',method=True,multi='_get_details'),
                
                'opening_balance_usd':fields.function(_get_detail,type='float',string='Opening USD',method=True,multi='_get_details'),
                'request_adv_usd':fields.function(_get_detail,type='float',string='Request Adv. USD',method=True,multi='_get_details'),
                'return_adv_usd':fields.function(_get_detail,type='float',string='Return Adv. USD',method=True,multi='_get_details'),
             }
    def init(self,cr):
        cr.execute("""-- Request ADV Amount
                        Create or replace view vwdetail_of_advance as 
                        (Select 
                            kap.name,
                            date_received_money as date,
                            payment_voucher_no as voucher_no,
                            kap.user_id,
                            staffno,
                            rr.name as user,
                            0 as debit,
                            request_amount as credit,
                            currency_id,
                            kcp.id as cash_period_id,
                            'Tạm Ứng / Advance Payment Cash No. ' || right(kap.name,2) as Description,
                            case when advance_buying<>'cash' then 'request_advance' else 'cash' end as type,
                            request_amount,
                            0 as return_amount
                        from
                            kderp_advance_payment kap
                        left join
                            kderp_cash_period kcp on date_received_money between date_start and date_stop
                        left join
                            hr_employee he on kap.user_id=he.id
                        left join
                            resource_resource rr on he.resource_id = rr.id
                        where 
                            advance_buying<>'cash' and kap.state not in ('draft','cancel')
                        Union
                        --Return ADV Amount
                        Select
                            kap.name,
                            date_of_received_reimbursement as date,
                            receive_voucher_no as voucher_no,
                            kap.user_id,
                            staffno,        
                            rr.name as user,
                            request_amount as debit,
                            0 as credit,
                            currency_id,
                            kcp.id as cash_period_id,
                            'Trả lại tạm ứng / Return Advance Payment Cash No.' || right(kap.name,2) as Description,
                            case when advance_buying<>'cash' then 'return_advance' else 'cash' end as type,
                            request_amount,
                            reimbursement_amount as return_amount
                        from
                            kderp_advance_payment kap
                        left join
                            kderp_cash_period kcp on date_of_received_reimbursement between date_start and date_stop
                        left join
                            hr_employee he on kap.user_id=he.id
                        left join
                            resource_resource rr on he.resource_id = rr.id
                        where 
                            advance_buying<>'cash' and kap.state not in ('draft','cancel','approved') and date_of_received_reimbursement is not null);""")
        cr.execute("""create or replace view 
                                    kderp_advance_check_detail_user_report as 
                        Select id,id as user_id from hr_employee;""")            
kderp_advance_check_detail_user_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
