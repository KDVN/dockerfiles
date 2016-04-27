# -*- encoding: utf-8 -*-
from openerp.osv import fields, osv

class kderp_gdt_update(osv.osv_memory):
    _name = 'kderp.gdt.update'
    _description = 'Update GDT Company'      
     
    def action_buttom_gdt_update(self, cr, uid, ids, context):
        tax_code = self.browse(cr, uid, ids[0], context).tax_code
        tax_code_id = self.search(cr, uid, [('tax_code','=',tax_code)])
        search_res = self.pool.get("gdt.companies.wizard")._query_data_from_gdt(tax_code)
        if search_res:
            action = self.pool.get("gdt.companies.wizard")._check_for_update(cr, uid, search_res)
            if action == 'update':
                self.write(cr,uid,tax_code_id,search_res,context)
            elif action == 'create':
                self.create(cr,uid,search_res,context)
            elif action == 'nothing':
                return False
        return True

kderp_gdt_update()