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

class kderp_upadate_history_price_wizard(osv.osv_memory):
    """
        This class using update price history in master list
    """
    _name = 'kderp.update.history.price.wizard'
    _description = 'KDERP Update history price'
    
    TYPE_PRICE = (('ref_avg','Average Price'),
                  ('ref_min','Min Price'),
                  ('ref_max','Max Price'),
                  ('ref_latest','Latest Price')
                  )
    SELECTION_RECORD = (('selected','Selected Record'),
                        ('record_ood','All record out of date with warning'),
                        ('record_diff','All record different with warning'),
                        ('record_na','All record not available with warning'),
                        ('all','All record in Master List')
                        )
    _columns = {
                'update_price':fields.selection(TYPE_PRICE, 'Price Type', required=True),
                'select_record':fields.selection(SELECTION_RECORD, 'Record Update', required=True),
                }
    _defaults={
               'update_price':'ref_avg',
               'select_record':lambda self, cr, uid, context={}: 'selected' if 'active_ids' in context else None 
               }
    
    def action_update_price(self, cr, uid, ids, context={}):
        """
            Update price from OpenERP to Reference price with selected type price Average, Min, Max price
        """
        
        popup_info = self.browse(cr, uid, ids[0], context)        
    
        if popup_info.select_record=='selected':
            pp_ids = context.get('active_ids', [])
            if not pp_ids:
                raise osv.except_osv("KDERP Warning", "Selected record not available !")
            pp_ids = ','.join(map(str, pp_ids))
            where_condition = 'id in (%s)' % pp_ids
        elif popup_info.select_record=='record_ood':
            where_condition = 'coalesce(outofdate, False)'
        elif popup_info.select_record=='record_diff':
            where_condition = 'coalesce(different, False)'
        elif popup_info.select_record=='record_na':
            where_condition = 'coalesce(not_available, False)'
        else: #Update All record
            where_condition = 'coalesce(master_list, False)'
        #Get product ids from condition
        cr.execute("""Select id from product_product where coalesce(master_list, False) and %s""" % where_condition)
        
        pp_ids = [pp_id[0] for pp_id in cr.fetchall()]
        
        #Update to log                
        cr.execute("""Update product_product set price = coalesce(%s,0) where coalesce(master_list, False) and %s""" % (popup_info.update_price, where_condition))
        import time
        self.pool.get('product.product').write(cr, uid, pp_ids, {'date_updated':time.strftime('%Y-%m-%d')}, context)
        
        return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }     

kderp_upadate_history_price_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
