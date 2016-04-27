# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _

class kderp_purchase_general_contract(osv.osv):
    _name='kderp.purchase.general.contract'    
    _description='KDERP Purchase General Contract'
    
    def name_get(self, cr, uid, ids, context=None):
        if not context: context={}
        res=[]
        for record in self.browse(cr, uid, ids):
            name = "%s - %s" % (record.name, record.date)  
            res.append((record['id'], name))
        return res    
    
    _columns={
              'partner_id':fields.many2one('res.partner','Supplier',ondelete='restrict',required=True),
              'name':fields.char('G.C. No.',size=16,select=1,required=True),
              'date':fields.date('G.C. Date',select=1,required=True),
              'description':fields.char('Desc.',size=128)
              }
    _defaults = {
                 'date': lambda *a: time.strftime('%Y-01-15'),
                 'partner_id':lambda self, cr, uid, context={}: context.get('partner_id',False)
                 }
    _sql_constraints=[('kderp_purchase_general_contract','unique(name)','General Contract Number and Date must be unique !')]
    
kderp_purchase_general_contract()

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns={
              'kderp_purchase_general_contract_ids':fields.one2many('kderp.purchase.general.contract','partner_id')
              }
res_partner()


class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'Purchase Order'
    
    # Them truong hop khi thay doi Supplier thi neu co hop dong chung thi se thay doi hop dong chung va ngay hop dong chung
    def onchange_partner_id(self, cr, uid, ids, partner_id,date=False):
        partner = self.pool.get('res.partner')

        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_term_id': False,
                'purchase_general_contract_id':False}}
        supplier_address = partner.address_get(cr, uid, [partner_id], ['default'])
        supplier = partner.browse(cr, uid, partner_id)
        
        cr.execute("""Select 
                            id
                    from 
                        kderp_purchase_general_contract 
                    where 
                        partner_id=%s and date=(select max(date) from kderp_purchase_general_contract where partner_id=%s)""" % (partner_id,partner_id))
        
        res = cr.fetchone()
        purchase_general_contract_id=False
        
        if res:
            purchase_general_contract_id = res[0]
            
        return {'value': {
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
            'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
            'payment_term_id': supplier.property_supplier_payment_term.id or False,
            'address_id': supplier.id or False,
            'purchase_general_contract_id':purchase_general_contract_id
            }}
                     
    _columns={
                'purchase_general_contract_id':fields.many2one('kderp.purchase.general.contract','G.C. No.',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),                
            }
purchase_order()