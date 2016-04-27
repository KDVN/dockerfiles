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
from openerp.osv import osv

class stock_init(osv.osv):
    _name = "kderp.config"
    _inherit = "kderp.config"
    
    location_dict = {'8':'HANOI', '4':'HCM'} #8 Connect to Hanoi, 4 Connect to HCM
    sqlTableDefinition = """id integer,
                            origin varchar(64),
                            product_code varchar(8),
                            product_qty numeric,
                            product_description varchar(256),
                            product_uom varchar(6),
                            price_unit numeric,
                            date timestamp,
                            move_description varchar(64),
                            stock_source varchar(32),
                            stock_destination varchar(32),
                            global_state varchar(16),
                            move_code integer,
                            source_move_code integer,
                            state varchar(16)"""
    sqlRemoteQuery = """Select 
                            sm.id,
                            sm.origin,
                            pp.default_code as product_code,
                            sm.product_qty,
                            sm.name as product_description,
                            pu.name as product_uom,
                            sm.price_unit,
                            sm.date,
                            aaa.code as move_description,
                            sls.stock_code as stock_source,
                            sld.stock_code as stock_destination,
                                sm.global_state,
                            sm.move_code,
                            sm.source_move_code,
                            sm.state
                        from 
                            stock_move sm
                        left join
                            product_product pp on sm.product_id = pp.id
                        left join
                            product_uom pu on sm.product_uom = pu.id
                        left join
                            stock_location sls on sm.location_id = sls.id
                        left join
                            stock_location sld on sm.location_dest_id = sld.id
                        left join
                            purchase_order_line pol on purchase_line_id = pol.id
                        left join
                            account_analytic_account aaa on pol.account_analytic_id = aaa.id
                        where
                             (sld.global_stock or sls.global_stock) and global_state <>''done'' and sm.state in (''done'',''confirmed'',''assigned'')"""
    tblLinkStock = 'stock_move'
    
    def init(self, cr):        
        from openerp import SUPERUSER_ID        
        kls_obj = self.pool.get('kderp.link.server')
        code_server = 'connection_to_%s' % self.location_dict[self.pool.get('res.users').browse(cr, SUPERUSER_ID, SUPERUSER_ID).company_id.location_code]
        kls_ids = kls_obj.search(cr, SUPERUSER_ID, [('name','=',code_server)])
        if not kls_ids: 
            vals = {}            
            vals['server'] = '172.16.10.192' if cr.dbname.count('HCM') else '192.168.1.11'
            vals['database'] = 'KDVN_Data_HN' if cr.dbname.count('HCM') else 'KDVN_Data_HCM'
            vals['user'] =  'stock_remote'
            vals['password'] = '290797!sr'
            vals['name'] = code_server
            kls_ids = [kls_obj.create(cr, SUPERUSER_ID, vals)]
        if kls_ids:
            klsl_obj = self.pool.get('kderp.link.server.line')
            code_server_line = code_server + "_stock_line"
            klsl_ids = klsl_obj.search(cr, SUPERUSER_ID, [('name','=', code_server_line)])
            if not klsl_ids:
                vals = {}
                vals['name'] = code_server_line
                vals['table_link_name'] = self.tblLinkStock 
                vals['table_definition'] = self.sqlTableDefinition
                vals['remote_query'] = self.sqlRemoteQuery
                vals['link_server_id'] = kls_ids[0]
                klsl_ids = [klsl_obj.create(cr, SUPERUSER_ID, vals)]
                klsl_obj.action_create_table_link(cr, SUPERUSER_ID, klsl_ids, {})
stock_init()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: