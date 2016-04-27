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

# 1 : imports of python lib
# 2 :  imports of openerp

#Stock Move State - Stock In
#    waiting: Waiting for Request Approval
#    confirmed: Waiting for Supplier Confirm
#    assigned: Waiting for Delivery
#    done: Received Already

def getSQLCommand(pool, cr, uid, stock_id, start_date, stop_date, period_id, key='list_available'):
    stp_obj = pool.get("kderp.stock.period")
    if key == 'list_available':
        # Move In - Product In
        sqlProductIn = """Select 
                            location_dest_id as location_id,
                            sm.product_id,
                            sm.product_uom,
                            sum(product_qty) as inp,
                            0 as out,
                            0 as available
                        from 
                            stock_move sm 
                        where 
                            location_dest_id = %s and sm.state='done' and sm.date between '%s' and '%s'
                        group by
                            location_dest_id,
                            sm.product_id,
                            sm.product_uom                        
                            """ % (stock_id ,start_date, stop_date)

        # Move Out - Product Out
        sqlProductOut = """Select 
                            location_id,
                            sm.product_id,
                            sm.product_uom,
                            0 as inp,
                            sum(product_qty) as out,
                            0 as available                            
                        from 
                            stock_move sm
                        where 
                            location_id = %s and sm.state='done' and sm.date between '%s' and '%s'
                        Group by
                            location_id,
                            sm.product_id,
                            sm.product_uom""" % (stock_id ,start_date, stop_date)
                            
        pre_id = stp_obj.find_pre_period_closed(cr, uid, start_date)['pre_period_id'] or 0
        #Available Product Previous Period        
        sqlAvailable = """Select 
                                location_id,
                                kspc.product_id,
                                kspc.product_uom,
                                0 as inp,
                                0 as out,
                                product_qty as available
                            from
                                kderp_stock_period_closed kspc
                            where
                                stock_period_id = %s and location_id = %s """ % (pre_id, stock_id)
        resultSQL = """location_id,                        
                        product_id,
                        product_uom,
                        %s stock_period_id,
                        sum(inp) + sum(available) - sum(out) as product_qty""" % period_id
        
        sqlCombine ="""Select 
                               %s
                        from
                            (%s
                            Union all
                            %s
                            Union all
                            %s) as vwcombine
                        group by
                            location_id,
                            product_id,
                            product_uom""" % (resultSQL,
                                              sqlProductIn, sqlProductOut, sqlAvailable)
        cr.execute(sqlCombine)
        return cr.dictfetchall()