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
from openerp.osv import fields, osv

class kderp_update_quotation_date(osv.osv_memory):
    _name = 'kderp.update.quotation.date'
    _description = 'Update Quotation Date'      
     
    def action_buttom_update_date(self, cr, uid, ids, context):
        cr.execute("""Select 
                            id,
                            completion_date_contract
                        from
                            sale_order so
                        where
                            completion_date is null and completion_date_contract is not null
                            """)       
        for so_id, so_date in cr.fetchall():           
            self.pool.get('sale.order').write(cr, uid, [so_id], {'completion_date': so_date})
        return True

kderp_update_quotation_date()