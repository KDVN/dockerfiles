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
from openerp.tools.translate import _

from dateutil.relativedelta import relativedelta
from datetime import datetime

class kderp_cash_fiscalyear(osv.osv):
    _name = "kderp.cash.fiscalyear"
    _description = "Cash Fiscal Year"    
    
    def action_close(self, cr, uid, ids, context=None):
        for kcf in self.browse(cr, uid, ids, context):
            for kcfl in kcf.period_ids:
                kcfl.write({'state':'done'})
        self.write(cr, uid, ids, {'state':'done'})
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def _get_ending_balance(self, cr, uid, ids, name, args, context={}):
        res={}
        for obj in self.browse(cr, uid, ids, context):            
            res[obj.id] = {'closing_balance_vnd_hanoi': 0.0,
                           'closing_balance_vnd_haiphong': 0.0,
                           'closing_balance_usd_hanoi': 0.0,
                           'closing_balance_usd_haiphong': 0.0,
                           }
            if obj.state <> 'draft':
                date_start=obj.date_start
                date_stop=obj.date_stop                
                cr.execute("""
                            Select
                                sum(case when substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1)='H' and rc.name='VND' then
                                    coalesce(debit,0)-coalesce(credit,0) else 0 end) + coalesce(pre_closing_balance_vnd_hanoi,0) as closing_balance_vnd_hanoi,
                                sum(case when substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1)='P' and rc.name='VND' then
                                    coalesce(debit,0)-coalesce(credit,0) else 0 end) + coalesce(pre_closing_balance_vnd_haiphong,0) as closing_balance_vnd_haiphong,
                                sum(case when substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1)='H' and rc.name='USD' then
                                    coalesce(debit,0)-coalesce(credit,0) else 0 end) + coalesce(pre_closing_balance_usd_hanoi,0) as closing_balance_usd_hanoi,
                                sum(case when substring(kdca.name from (case when type='cash' then 2 else 3 end) for 1)='P' and rc.name='USD' then
                                    coalesce(debit,0)-coalesce(credit,0) else 0 end) + coalesce(pre_closing_balance_usd_haiphong,0) as closing_balance_usd_haiphong    
                            from
                                kderp_detail_cash_advance kdca
                            left join
                                res_currency rc on currency_id=rc.id
                            left join
                                (
                                Select
                                    case when state='draft' then 0 else closing_balance_vnd_hanoi end as pre_closing_balance_vnd_hanoi,
                                    case when state='draft' then 0 else closing_balance_vnd_haiphong end as pre_closing_balance_vnd_haiphong,
                                    case when state='draft' then 0 else closing_balance_usd_hanoi end as pre_closing_balance_usd_hanoi,
                                    case when state='draft' then 0 else closing_balance_usd_haiphong end as pre_closing_balance_usd_haiphong
                                from
                                    kderp_cash_fiscalyear kcf
                                where    
                                    kcf.date_stop = (select 
                                                max(date_stop) 
                                               from 
                                                kderp_cash_fiscalyear kcf 
                                               where
                                                date_stop<'%s')) vwprevious on 1=1
                            where    
                                kdca.date between '%s' and '%s'
                            group by
                                pre_closing_balance_vnd_hanoi,
                                pre_closing_balance_vnd_haiphong,
                                pre_closing_balance_usd_hanoi,
                                pre_closing_balance_usd_haiphong""" % (
                                                                       date_start,
                                                                       date_start, date_stop))
            result=cr.dictfetchone()
            if result:
                res[obj.id]=result                         
        return res
    
    _columns = {
        'name': fields.char('Fiscal Year', size=64, required=True),
        'code': fields.char('Code', size=6, required=True),
        'date_start': fields.date('Start Date', required=True),
        'date_stop': fields.date('End Date', required=True),
        'period_ids': fields.one2many('kderp.cash.period', 'kderp_cash_fiscalyear_id', 'Periods'),
        'state': fields.selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True),
        'closing_balance_vnd_hanoi':fields.function(_get_ending_balance, type='float',method=True, multi='_get_ending_balance', store=
                                                    {
                                                     'kderp.cash.fiscalyear': (lambda self, cr, uid, ids, context:ids, None, 15),
                                                     }),
        'closing_balance_usd_hanoi':fields.function(_get_ending_balance, type='float',method=True, multi='_get_ending_balance', store=
                                                    {
                                                     'kderp.cash.fiscalyear': (lambda self, cr, uid, ids, context:ids, None, 15),
                                                     }),
        'closing_balance_vnd_haiphong':fields.function(_get_ending_balance, type='float',method=True, multi='_get_ending_balance', store=
                                                    {
                                                     'kderp.cash.fiscalyear': (lambda self, cr, uid, ids, context:ids, None, 15),
                                                     }),
        'closing_balance_usd_haiphong':fields.function(_get_ending_balance, type='float',method=True, multi='_get_ending_balance', store=
                                                    {
                                                     'kderp.cash.fiscalyear': (lambda self, cr, uid, ids, context:ids, None, 15),
                                                     })
    }
    _defaults = {
        'state': 'draft'
    }
    _order = "date_start, id"


    def _check_duration(self, cr, uid, ids, context=None):
        obj_fy = self.browse(cr, uid, ids[0], context=context)
        if obj_fy.date_stop < obj_fy.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error!\nThe start date of a fiscal year must precede its end date.', ['date_start','date_stop'])
    ]

    def create_period3(self, cr, uid, ids, context=None):
        return self.create_period(cr, uid, ids, context, 3)

    def create_period(self, cr, uid, ids, context=None, interval=1):
        period_obj = self.pool.get('kderp.cash.period')
        for fy in self.browse(cr, uid, ids, context=context):
            ds = datetime.strptime(fy.date_start, '%Y-%m-%d')
#             period_obj.create(cr, uid, {
#                     'name':  "%s %s" % (_('Opening Period'), ds.strftime('%Y')),
#                     'code': ds.strftime('00/%Y'),
#                     'date_start': ds,
#                     'date_stop': ds,
#                     'special': True,
#                     'kderp_cash_fiscalyear_id': fy.id,
#                 })
            while ds.strftime('%Y-%m-%d') < fy.date_stop:
                de = ds + relativedelta(months=interval, days=-1)

                if de.strftime('%Y-%m-%d') > fy.date_stop:
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')

                period_obj.create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'kderp_cash_fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    def find(self, cr, uid, dt=None, exception=True, context=None):
        res = self.finds(cr, uid, dt, exception, context=context)
        return res and res[0] or False

    def finds(self, cr, uid, dt=None, exception=True, context=None):
        if context is None: context = {}
        if not dt:
            dt = fields.date.context_today(self,cr,uid,context=context)
        args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]

        ids = self.search(cr, uid, args, context=context)
        if not ids:
            if exception:
                raise osv.except_osv(_('Error!'), _('There is no fiscal year defined for this date.\nPlease create one from the configuration of the accounting menu.'))
            else:
                return []
        return ids

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        if args is None:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('code', 'ilike', name)]+ args, limit=limit)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit)
        return self.name_get(cr, user, ids, context=context)
    
kderp_cash_fiscalyear()

class kderp_cash_period(osv.osv):
    _name = "kderp.cash.period"
    _description = "KDERP Cash Period"
    
#     def _get_this_balance_period(self, cr, uid, ids, name, args, context={}):
#         if not context:
#             context={}
#         kcp_ids=",".join(map(str,ids))
#         res={}
#         cr.execute("""Select 
#                         kcp.id,
#                         sum(case when coalesce(rc.name,'')='VND' then coalesce(debit,0)-coalesce(credit,0) else 0 end ) as balance_this_period_vnd,
#                         sum(case when coalesce(rc.name,'')='USD' then coalesce(debit,0)-coalesce(credit,0) else 0 end ) as balance_this_period_usd
#                     from 
#                         kderp_cash_period kcp
#                     left join
#                         kderp_detail_cash_advance kdca on kcp.id=cash_period_id
#                     left join
#                         res_currency rc on currency_id=rc.id
#                     where
#                         kcp.id in (%s)
#                     Group by
#                         kcp.id;""" % kcp_ids)
#         for kcp_obj in cr.dictfetchall():
#             res[kcp_obj.pop('id')]=kcp_obj
#         return res
    
#     def _get_cash_period(self, cr, uid, ids, context):
#         if not context:
#             context={}
#         #context['from_current']=True
#         
#         kcp_ids=ids
# #         for kcp_obj in self.browse(cr, uid, ids, context):
# #             kcp_ids.extend(self.find(cr, uid, kcp_obj.date_start,context))
# #             
# #         kcp_ids=list(set(kcp_ids))
#         #kcp_ids=self.search(cr, uid, [('id','in',kcp_ids)])        
#         return kcp_ids
  
#     def _get_previous_period(self, cr, uid, ids, name, args, context={}):
#         if not context:
#             context={}
#         kcp_ids=",".join(map(str,ids))
#         res={}
#         cr.execute("""Select
#                         kcp.id,
#                         vwtemp.ending_balance_vnd,
#                         vwtemp.ending_balance_usd,
#                         vwtemp_pre.previous_ending_balance_vnd,
#                         vwtemp_pre.previous_ending_balance_usd
#                     from
#                         kderp_cash_period kcp
#                     left join
#                         (Select 
#                             kcp.id,
#                             lag(id) over (order by date_start asc) as previous_id,
#                             sum(coalesce(balance_this_period_vnd,0)) over (order by date_start) as ending_balance_vnd,
#                             sum(coalesce(balance_this_period_usd,0)) over (order by date_start) as ending_balance_usd
#                         from 
#                             kderp_cash_period kcp
#                         Group by
#                             kcp.id
#                         order by 
#                             date_start) vwtemp on kcp.id=vwtemp.id
#                     left join
#                         (Select 
#                                 kcp.id,
#                                 sum(coalesce(balance_this_period_vnd,0)) over (order by date_start) as previous_ending_balance_vnd,
#                                 sum(coalesce(balance_this_period_usd,0)) over (order by date_start) as previous_ending_balance_usd
#                             from 
#                                 kderp_cash_period kcp
#                             Group by
#                                 kcp.id
#                             order by 
#                                 date_start) vwtemp_pre on previous_id=vwtemp_pre.id
#                         where kcp.id in (%s)""" % (kcp_ids))
#                 
#         for kcp_obj in cr.dictfetchall():
#             res[kcp_obj.pop('id')] = kcp_obj            
#         return res
    
    _columns = {
        'detail_ids':fields.one2many('kderp.detail.cash.advance','cash_period_id','Details',readonly="1"),
        'name': fields.char('Period Name', size=64, required=True),
        'code': fields.char('Code', size=12),
        'kderp_cash_fiscalyear_id': fields.many2one('kderp.cash.fiscalyear', 'Fiscal Year', required=True, states={'done':[('readonly',True)]}, select=True),
        'special': fields.boolean('Opening/Closing Period', size=12,
            help="These periods can overlap."),
        'date_start': fields.date('Start of Period', required=True, states={'done':[('readonly',True)]}),
        'date_stop': fields.date('End of Period', required=True, states={'done':[('readonly',True)]}),        
        'state': fields.selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True,
                                  help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.'),
#         'balance_this_period_vnd':fields.function(_get_this_balance_period,string="Balance VND",type='float',method=True,multi='_get_this_balance',
#                                                   store={
#                                                          'kderp.cash.period': (lambda self, cr, uid, ids, context:ids, None, 30),
#                                                          }),
#                 
#         'balance_this_period_usd':fields.function(_get_this_balance_period,string="Balance USD",type='float',method=True,multi='_get_this_balance',
#                                                   store={
#                                                          'kderp.cash.period': (lambda self, cr, uid, ids, context:ids, None, 30),
#                                                          }),
#         'previous_ending_balance_vnd':fields.function(_get_previous_period,string="Pre. Ending Balance VND",type='float',method=True,multi='_get_previous_balance',
#                                                   store={
#                                                          'kderp.cash.period': (_get_cash_period, ['date_start','date_stop'], 35),
#                                                          }),
#         'previous_ending_balance_usd':fields.function(_get_previous_period,string="Pre. Ending Balance USD",type='float',method=True,multi='_get_previous_balance',
#                                                   store={
#                                                          'kderp.cash.period': (_get_cash_period, ['date_start','date_stop'], 35),
#                                                          }),
#         
#         'ending_balance_vnd':fields.function(_get_previous_period,string="Ending Balance VND",type='float',method=True,multi='_get_previous_balance',
#                                                   store={
#                                                          'kderp.cash.period': (_get_cash_period, ['date_start','date_stop'], 35),
#                                                          }),
#         'ending_balance_usd':fields.function(_get_previous_period,string="Ending Balance USD",type='float',method=True,multi='_get_previous_balance',
#                                                   store={
#                                                          'kderp.cash.period': (_get_cash_period, ['date_start','date_stop'], 35),
#                                                          }),
    }
    _defaults = {
        'state': 'draft',
    }
    _order = "kderp_cash_fiscalyear_id desc, date_start"
    _sql_constraints = [
        ('name_period_cash_unique', 'unique(name, date_start)', 'The name of the period must be unique per company!'),
    ]

    def _check_year_limit(self,cr,uid,ids,context=None):
        for obj_period in self.browse(cr, uid, ids, context=context):
            if obj_period.special:
                continue

            if obj_period.kderp_cash_fiscalyear_id.date_stop < obj_period.date_stop or \
               obj_period.kderp_cash_fiscalyear_id.date_stop < obj_period.date_start or \
               obj_period.kderp_cash_fiscalyear_id.date_start > obj_period.date_start or \
               obj_period.kderp_cash_fiscalyear_id.date_start > obj_period.date_stop:
                return False

        return True
    
    def _check_duration(self,cr,uid,ids,context=None):
        obj_period = self.browse(cr, uid, ids[0], context=context)
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True
    
    _constraints = [
        (_check_duration, 'Error!\nThe duration of the Period(s) is/are invalid.', ['date_stop']),
        (_check_year_limit, 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.', ['date_stop'])
    ]
        
    def action_kderp_cash_period_close(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'})
        return True

    def next(self, cr, uid, period, step, context=None):
        ids = self.search(cr, uid, [('date_start','>',period.date_start)])
        if len(ids)>=step:
            return ids[step-1]
        return False
# 
#     def find(self, cr, uid, dt=None, context=None):
#         if context is None: context = {}
#         if not dt:
#             dt = fields.date.context_today(self, cr, uid, context=context)
#         args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
#         
# #         if context.get('company_id', False):
# #             args.append(('company_id', '=', context['company_id']))
# #         else:
# #             company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
# #             args.append(('company_id', '=', company_id))
#         result = []
#         
#         if context.get('account_period_prefer_normal'):
#             # look for non-special periods first, and fallback to all if no result is found
#             result = self.search(cr, uid, args + [('special', '=', False)], context=context)
#         if not result:
#             result = self.search(cr, uid, args, context=context)
#         if not result:
#             raise osv.except_osv(_('Error!'), _('There is no period defined for this date: %s.\nPlease create one.')%dt)
#         return result
#     
    def find(self, cr, uid, dt=None, context=None, prev=False):
        if context is None: context = {}
         
        if not dt and not prev:
            dt = fields.date.context_today(self, cr, uid, context=context)
        elif not dt and prev:
            import datetime
            today = datetime.date.today()
            first = datetime.date(day=1, month=today.month, year=today.year)
            lastMonth = first - datetime.timedelta(days=1)
            dt = lastMonth.strftime("%Y-%m-%d")
        if context.get('from_current',False):
            args = [('date_stop', '>=', dt)]
        else:
            args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
         
        result = []
 
        if not result:
            result = self.search(cr, uid, args+[('state','=','draft')], context=context)
        if not result:
            raise osv.except_osv(_('Error!'), _('There is no period defined for this date: %s.\nPlease create one.')%dt)
        return result

    def action_draft(self, cr, uid, ids, *args):
        mode = 'draft'
        for period in self.browse(cr, uid, ids):
            if period.kderp_cash_fiscalyear_id.state == 'done':
                raise osv.except_osv(_('Warning!'), _('You can not re-open a period which belongs to closed fiscal year'))
        cr.execute('update kderp_cash_period set state=%s where id in %s', (mode, tuple(ids),))
        return True

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if args is None:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user,
                              [('code', 'ilike', name)] + args,
                              limit=limit,
                              context=context)
        if not ids:
            ids = self.search(cr, user,
                              [('name', operator, name)] + args,
                              limit=limit,
                              context=context)
        return self.name_get(cr, user, ids, context=context)


kderp_cash_period()