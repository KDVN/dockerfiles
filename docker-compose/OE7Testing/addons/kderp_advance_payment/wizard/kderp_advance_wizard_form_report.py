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

class kderp_advance_wizard_cash_form(osv.osv_memory):
    _name = 'kderp.advance.wizard.cash.form'
    _description = 'KDERP Advance Wizard Print Cash Payment Form'      
    
    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids',[]),
                 'parameters':{'pVAT':self.browse(cr, uid, ids[0]).pVAT,
                               'pEXRATE':self.browse(cr, uid, ids[0]).pEXRATE,
                               'pCUR':self.browse(cr, uid, ids[0]).currency_id.name,}                
                 }
        
        datas['model'] = 'kderp.advance.payment'
        datas['title'] = 'Advance Cash Payment Form'
        
        report_name='kderp.report.cash.payment.advance.pdf'
         
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas}
     
    _columns = {                
                'pVAT':fields.float('VAT Amount',required=1),
                'pEXRATE':fields.float('Exchange Rate',required=1),
                'currency_id': fields.many2one("res.currency", string="Currency", required=True)
                }
    
    _defaults = {
                'pVAT':0.0,
                'currency_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id,
                'pEXRATE':lambda self, cr, uid, context={}: 1.0 if 'currency_id' not in context else None
                }
kderp_advance_wizard_cash_form()