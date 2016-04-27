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

import time
        
class kderp_fixed_assets_report_wizard(osv.osv_memory):
    _name = 'kderp.fixed.assets.report'
    _description = 'KDERP Fixed Assets Report Wizard'
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
            res.append((elmt.id,"Fixed Assets report %s ~ %s" % (from_date,to_date)))
        return res
    
    def onchange_date(self, cr, uid, ids, date_start,date_stop, context={}):
        result={'detail_ids':[]}
        import datetime
        if date_start:
            actual_start_date=datetime.datetime.strptime(date_start, "%Y-%m-%d")
        if date_stop:
            actual_stop_date=datetime.datetime.strptime(date_stop, "%Y-%m-%d")
        
        if date_start:
            compare_date=datetime.datetime.strptime('2014-01-01', "%Y-%m-%d")
            if actual_start_date<compare_date:
                raise osv.except_osv("KDERP Warning",'You must input Start Date greater than or equal to 01-Jan-2014, Thank you')
            
        if date_start and date_stop:
            if actual_start_date>=actual_stop_date:
                raise osv.except_osv("KDERP Warning",'You must input Start Date less than Stop Date, Thank you')
            
            cr.execute("""Select 
                            kam.id
                        from
                            kderp_asset_management kam
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        where
                            (state not in ('draft','liquidated')  or (state='liquidated' and dateofliquidated between '%s' and '%s') ) and 
                            ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and 
                            dateofinvoice<='%s'""" % (date_start,date_stop,date_stop))
            detail_ids = [x[0] for x in cr.fetchall()]
            result={'detail_ids':detail_ids}            
        return {'value':result}
     
    def compute(self, cr, uid, ids, context=None):
        return {
                'tag': 'reload',
                'type': 'ir.actions.act_window_close' 
                }
    
    def action_open_detail(self, cr, uid, ids, context=None):
        if not context:
            context={}
        data = self.read(cr, uid, ids, ['date_start','date_stop','detail_ids'],context=context)[0]
        detail_ids=data['detail_ids']
        
        context.update({'date_start': data['date_start'],
                 'date_stop':data['date_stop']})
        context.update({'group_by':['assettype','assetcode']})
        
        return {
            'domain': "[('id','in',[%s])]" % (",".join(map(str,detail_ids))),
            'name': 'Fixed Assets Report',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'context':context,
            'res_model': 'kderp.fixed.assets.detail.report',
            'type': 'ir.actions.act_window'
            }
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': ids}
        datas['model'] = 'kderp.fixed.assets.report'
        datas['title'] = 'Fixed Assets Report'
        for pr in self.browse(cr, uid, ids):
            if pr.excel:
                report_name='kderp.report.fixed.asset.xls'
            else:
                report_name='kderp.report.fixed.asset'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas}
            
    def _get_detail_list(self, cr, uid, ids, name, args, context={}):
        res={}
        for obj in self.browse(cr, uid, ids, context):
            date_start=obj.date_start
            date_stop=obj.date_stop
            only_hcm = obj.only_hcm
            only_hanoi = obj.only_hanoi
            
            if only_hcm and only_hanoi:
                new_condition=False
            elif self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.name.find('HCM')>=0:
                new_condition=True
            elif only_hcm:
                new_condition="coalesce(refcode,'') ilike '%%For%%HCM%%'"
            elif only_hanoi:
                new_condition="coalesce(refcode,'') not ilike '%%For%%HCM%%'"
            else:
                new_condition=True
            
            res[obj.id]=[]
            if date_start and date_stop:
                cr.execute("""Select 
                                kam.id
                            from
                                kderp_asset_management kam
                            left join
                                kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                            left join
                                kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                            where
                                (state not in ('draft','liquidated')  or (state='liquidated' and (dateofliquidated between '%s' and '%s' or dateofliquidated>'%s'))) and 
                                ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and dateofinvoice<='%s' and %s""" % (date_start,date_stop,date_stop,date_stop,new_condition))
                for uid in cr.fetchall():
                    res[obj.id].append(uid[0])
                res[obj.id]=list(set(res[obj.id]))                        
            return res
        
    def _get_datestart(self, cr, uid, context):
        from datetime import date
        res = date(date.today().year, 1, 1).strftime('%Y-%m-%d')
        return res
        
    _columns = {                
                'date_start':fields.date('Start Date',required=1),
                'date_stop':fields.date('Stop Date',required=1),
                'detail_ids':fields.function(_get_detail_list,obj='kderp.fixed.assets.detail.report',type='one2many',string='Details',method=True),
                'excel':fields.boolean("Excel File?"),
                'only_hanoi':fields.boolean("Hanoi Only?"),
                'only_hcm':fields.boolean("HCM Only?"),                
                }
    _defaults = {
                'excel':True,
                'detail_ids':[],
                'date_stop':lambda *a: time.strftime('%Y-%m-%d'),
                'date_start':_get_datestart,
                'only_hanoi':lambda self, cr, uid, context={}: self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.name.find('HCM')<0,
                #'only_hcm':lambda self, cr, uid, context={}: self.pool.get('res.users').browse(cr, uid, uid).company_id.partner_id.name.find('HCM')>=0
                }
kderp_fixed_assets_report_wizard()

class kderp_fixed_assets_detail_report(osv.osv):
    _name='kderp.fixed.assets.detail.report'
    _auto=False
    _rec_name='asset_id'
    
    def _get_detail(self, cr, uid, ids, name, args, context={}):
        res={}
        if not context:
            context={}
        #raise osv.except_osv("E",context)
        for id in ids:
            res[id]={'original_price':0,'depreciation':0,'reduce':0,
                     'accumulated_depreciation':0}
        date_start=context.get('date_start',False)
        date_stop=context.get('date_stop',False)
        
        only_hanoi = context.get('only_hanoi',False)
        only_hcm = context.get('only_hcm',False)
        
        if (not date_start or not date_stop) and context.get('active_id',False):          
            main_id=context.get('active_id',0)
            main_obj=self.pool.get('kderp.fixed.assets.report').browse(cr, uid, main_id, context)
            date_start=main_obj.date_start
            date_stop=main_obj.date_stop
            only_hcm = main_obj.only_hcm
            only_hanoi = main_obj.only_hanoi
            
        if only_hcm and only_hanoi:
            new_condition=False
        elif only_hcm:
            new_condition="coalesce(refcode,'') ilike '%%For%%HCM%%'"
        elif only_hanoi:
            new_condition="coalesce(refcode,'') not ilike '%%For%%HCM%%'"
        else:
            new_condition=True

        if not date_start or not date_stop:
            return res
        
        #Query tra ve gia tri tinh khau hao:
        # 1. Khau hao tat ca trong ky: 
        #                               Reduce (KH Trong ky giam) = 0
        #                               Depreciation (KH Trong ky) = Sum(amount) trong ky
        #                               KH Luy Ke = 0
        # 2. Khau hao tung phan trong ky: 
        #                               Reduce (KH Trong ky giam) = Amount trong Partial Liquidation 
        #                               Depreciation (KH Trong ky) = Sum(amount) trong ky
        #                               KH Luy Ke = Sum(Khau hao ky truoc) - Reduce
        #                               Original Price = Actual Original - Sum(amount partial liquidation)
        # 3. Truong hop khau hao trong ky nhung van con gia tri (chua khau hao het 100%)
        # Gia tri khau hao trong ky = TONG GIA TRI KHAU HAO TRONG KY + REMAINING VALUE neu so tien remaining cua ky truoc >0, neu =0 thi gia tri la 0
        cr.execute("""Select 
                        kam.id as asset_id,
                        price*quantity-coalesce(partial_accumulated_amount,0) as original_price,
                        case when old_code='EQ1008-2' and '2014-01-01' between '%s' and '%s' then 56622500 else sum(coalesce(kad.amount,0)) end as depreciation,
                        coalesce(partial_accumulated_amount,0) as reduce,
                        previous_depreciation+sum(coalesce(kad.amount,0))-coalesce(partial_accumulated_amount,0) as accumulated_depreciation
                    from
                        kderp_asset_management kam
                    left join
                        (Select 
                            kam.id,
                            sum(coalesce(kapl.amount,0)) as partial_accumulated_amount
                        from 
                            kderp_asset_management kam
                        left join
                            kderp_asset_partial_liquidation kapl on kam.id=kapl.asset_id
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        where
                           state not in ('draft','liquidated') and ktoa.name='FA' and kapl.date between '%s' and '%s' and %s --DK1
                        Group by
                            kam.id) vwpartial_liquidation on kam.id = vwpartial_liquidation.id 
                    left join
                        kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                    left join
                        kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                    left join
                        kderp_asset_depreciation kad on kam.id=asset_id and kad.date between '%s' and '%s' --DK2
                    left join
                        (select 
                            kam.id,
                            kam.code,
                            sum(coalesce(kado.amount,0))+(case when using_remaining then price*quantity -remaining_amount else 0 end) as previous_depreciation
                        from
                            kderp_asset_management kam
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        left join
                            kderp_asset_depreciation kado on kam.id=asset_id and kado.date<'%s' --DK4
                        where
                            state not in ('draft','liquidated') and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and %s --DK5
                        group by
                            kam.id) vwold on kam.id=vwold.id
                    where
                        state not in ('draft','liquidated') and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and dateofinvoice<='%s' and %s --DK6
                    group by
                        kam.id,
                        previous_depreciation,
                        coalesce(partial_accumulated_amount,0)
                    Union
                    Select 
                        kam.id as asset_id,
                        0 as original_price,
                        sum(coalesce(kad.amount,0)) + coalesce(partial_accumulated_amount,0)
                        + coalesce(price*quantity,0) - coalesce(previous_depreciation,0) - coalesce(partial_accumulated_amount,0) - sum(coalesce(kad.amount,0)) as depreciation,
                        --((case when using_remaining then price*quantity -remaining_amount else 0 end)+sum(coalesce(kad.amount,0))) 
                        --end as depreciation,
                        
                        price*quantity as reduce,-- -sum(coalesce(kad.amount,0))
                        0 as accumulated_depreciation
                    from
                        kderp_asset_management kam
                    left join
                        (Select 
                            kam.id,
                            sum(coalesce(kapl.amount,0)) as partial_accumulated_amount
                        from 
                            kderp_asset_management kam
                        left join
                            kderp_asset_partial_liquidation kapl on kam.id=kapl.asset_id
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        where
                             state='liquidated' and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and kapl.date between '%s' and '%s' and %s --DK6.1
                        Group by
                            kam.id) vwpartial_liquidation on kam.id = vwpartial_liquidation.id
                    LEFT JOIN
                        (select 
                            kam.id,
                            sum(coalesce(kado.amount,0))+(case when using_remaining then price*quantity -remaining_amount else 0 end) as previous_depreciation
                        from
                            kderp_asset_management kam
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        left join
                            kderp_asset_depreciation kado on kam.id=asset_id and kado.date<'%s' --DK6.2
                        where
                           state='liquidated' and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code)  and dateofliquidated between '%s' and '%s' and %s --DK6.3
                        group by
                            kam.id) vwold on kam.id=vwold.id
                    left join
                        kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                    left join
                        kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                    left join
                        kderp_asset_depreciation kad on kam.id=asset_id and kad.date between '%s' and '%s' --DK7
                    where
                        state='liquidated' and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and dateofliquidated between '%s' and '%s' and %s --DK8
                    group by
                        kam.id,
                        coalesce(previous_depreciation,0),
                        coalesce(partial_accumulated_amount,0)
                    Union
                    Select 
                        kam.id as asset_id,
                        price*quantity-coalesce(partial_accumulated_amount,0) as original_price,
                        case when old_code='EQ1008-2' then 56622500 else sum(coalesce(kad.amount,0)) end as depreciation,
                        coalesce(partial_accumulated_amount,0) as reduce,
                        previous_depreciation+sum(coalesce(kad.amount,0))-coalesce(partial_accumulated_amount,0) as accumulated_depreciation
                    from
                        kderp_asset_management kam
                    left join
                        (Select 
                            kam.id,
                            sum(coalesce(kapl.amount,0)) as partial_accumulated_amount
                        from 
                            kderp_asset_management kam
                        left join
                            kderp_asset_partial_liquidation kapl on kam.id=kapl.asset_id
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        where
                            state ='liquidated' and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and kapl.date between '%s' and '%s' and %s --DK9
                        Group by
                            kam.id) vwpartial_liquidation on kam.id = vwpartial_liquidation.id
                    left join
                        kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                    left join
                        kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                    left join
                        kderp_asset_depreciation kad on kam.id=asset_id and kad.date between '%s' and '%s' --DK10
                    left join
                        (select 
                            kam.id,
                            kam.code,
                            sum(coalesce(kado.amount,0))+(case when using_remaining then price*quantity -remaining_amount else 0 end) as previous_depreciation
                        from
                            kderp_asset_management kam
                        left join
                            kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                        left join
                            kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                        left join
                            kderp_asset_depreciation kado on kam.id=asset_id and kado.date<'%s' --DK11
                        where
                             state ='liquidated' and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and %s --DK12
                        group by
                            kam.id) vwold on kam.id=vwold.id
                    where
                        state ='liquidated' and ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code) and dateofliquidated>'%s' and %s --DK13
                    group by
                        kam.id,
                        previous_depreciation,
                        coalesce(partial_accumulated_amount,0)
                        """ % (date_start,date_stop,
                               date_start,date_stop,new_condition,#DK1
                               date_start,date_stop, #DK2
                               date_start,#DK4
                               new_condition,#DK5
                               date_stop,new_condition,#DK6
                               date_start,date_stop,new_condition,#DK6.1
                               date_start,#DK6.2
                               date_start,date_stop,new_condition,#DK6.3
                               date_start,date_stop,#DK7
                               date_start,date_stop,new_condition,#DK8
                               date_start,date_stop,new_condition,#DK9
                               date_start,date_stop,#DK10
                               date_start,#DK11
                               new_condition,#DK12
                               date_stop,new_condition#DK13
                               ))
        for obj in cr.dictfetchall():
            res[obj.pop('asset_id')]=obj
        return res
    
    _columns={
                'asset_id':fields.many2one('kderp.asset.management','Asset'),#function(_get_detail,type='many2one',string='Asset',relation='kderp.asset.management',method=True,multi='_get_details'),
                'original_price':fields.function(_get_detail,type='float',string='Original',method=True,multi='_get_details'),
                'depreciation':fields.function(_get_detail,type='float',string='Depreciation',method=True,multi='_get_details'),
                'reduce':fields.function(_get_detail,type='float',string='Reduce',method=True,multi='_get_details'),
                'accumulated_depreciation':fields.function(_get_detail,type='float',string='Accumulated Depreciation',method=True,multi='_get_details'),
                'liquidated_amount':fields.function(_get_detail,type='float',string='Liquidation Amt.',method=True,multi='_get_details'),
                'assettype':fields.char('Asset Type',size=16),
                'assetcode':fields.char('Asset Code',size=64),                                
                'oldcode':fields.char('Old Code',size=32),
             }

    def init(self,cr):
        cr.execute("""
                    create or replace view kderp_fixed_assets_detail_report as 
                    Select 
                        kam.id as id,
                        kam.id as asset_id,
                        kaca.name as assetcode,
                        case when type='1' then 'Tangible' else case when type='2' then 'Intangible' else 'Others' end end as assettype,
                        old_code as oldcode
                    from
                        kderp_asset_management kam
                    left join
                        kderp_asset_code_accounting kaca on kam.type_asset_acc_id=kaca.id
                    left join
                        kderp_type_of_asset ktoa on kaca.typeofasset_id=ktoa.id
                    --left join
                    --    kderp_asset_depreciation kad on kam.id=asset_id
                    where
                        ktoa.name='FA' and length('HFA1-13-14-0001')=length(kam.code)""")            
kderp_fixed_assets_detail_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
