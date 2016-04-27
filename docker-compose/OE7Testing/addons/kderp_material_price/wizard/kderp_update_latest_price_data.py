# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv

class kderp_update_price_data(osv.osv_memory):
    _name='kderp.update.price.data'
    _description = "KDERP Update Price Data from Purchase"
    
    def action_update_latest_price(self, cr, uid, ids=False, context=False):
        #Update latest price to Product
        limit_date = self.pool.get('res.users').browse(cr, uid, uid).company_id.price_history_after_days_ood
        limit_date = limit_date if limit_date else 0        
        
        cr.execute("""Update 
                        product_product pp
                    set
                        latest_date = vwdata.latest_date,
                        ref_latest = vwdata.latest_price,
                        ref_min = vwdata.ref_min,
                        ref_avg = vwdata.ref_avg,
                        ref_max = vwdata.ref_max,
                        outofdate = (now()::date - date_updated::date - %s)>=0
                    from
                        (Select 
                            pp.id,
                            max(date_order) as latest_date,
                            max(price_unit* fnpo_compute(ppr.currency_id, (select currency_id from res_company  limit 1), po.date_order)) as ref_max,
                            avg(price_unit* fnpo_compute(ppr.currency_id, (select currency_id from res_company  limit 1), po.date_order)) as ref_avg,
                            min(price_unit* fnpo_compute(ppr.currency_id, (select currency_id from res_company  limit 1), po.date_order)) as ref_min,
                            latest_price
                        from        
                            product_product pp 
                        left join
                            purchase_order_line pol  on pp.id = product_id
                        left join
                            purchase_order po on pol.order_id = po.id
                        left join
                            product_pricelist ppr on po.pricelist_id = ppr.id
                        left join
                             (Select
                                    product_id as pp_id,
                                    last(pol.price_unit * fnpo_compute(ppr.currency_id, (select currency_id from res_company  limit 1), po.date_order)) as latest_price
                                from
                                    purchase_order_line pol
                                left join
                                    purchase_order po on order_id = po.id
                                left join
                                    product_pricelist ppr on po.pricelist_id = ppr.id
                                Where (product_id, po.date_order) in 
                                    (Select 
                                        product_id,
                                        max(po.date_order) as aaa
                                    from
                                        purchase_order_line pol
                                    left join
                                        purchase_order po on pol.order_id = po.id            
                                    where 
                                        po.date_order is not null and po.state not in ('draft','cancel') 
                                    group by 
                                        product_id)
                                group by
                                    product_id 
                             ) vwtemp2 on pp.id = pp_id
                        where
                            po.state not in ('draft','cancel') and 
                            date_order>=coalesce(date_updated, now() - interval '1 year') and
                            coalesce(master_list,False)
                        Group by
                            pp.id,latest_price) vwdata
                    where
                        pp.id = vwdata.id""" % limit_date)        
       
        return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
kderp_update_price_data()