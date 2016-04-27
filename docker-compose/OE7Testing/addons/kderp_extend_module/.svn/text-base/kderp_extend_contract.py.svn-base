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

class kderp_contract_client(osv.osv):
    _name='kderp.contract.client'
    _description='KDERP Contract to Client'
    _inherit = 'kderp.contract.client'
    
    def action_open_contract_state(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'uncompleted'})
        return True
        
    def action_contract_cancelled(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'availability':'cancelled'})
        return True
    
    def action_contract_inused(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'availability':'inused'})
        return True
    
    def onchange_reg_date(self, cr, uid, ids,registration_date,revise_date):
        val={}
        if not revise_date and self.pool.get('res.users').browse(cr, uid, uid, {}).location_user=='hanoi':
            val={'revise_date':registration_date}
        return {'value':val}
    
    def onchange_client_id(self, cr, uid, ids, client_id):
        if not client_id:
            val={}
        else:
            rp_obj=self.pool.get('res.partner').browse(cr, uid, client_id)
            invoice=False
            invoice_address_id=False
            address_id=False
            
            last_address_id=False
                        
            for rpl in rp_obj.child_ids:
                if rpl.type=='invoice':
                    invoice_address_id=rpl.id
                    invoice=True
                if rpl.type=='default':
                    if not invoice:
                        invoice_address_id=rpl.id
                    address_id = rpl.id
                last_address_id=rpl.id
            if not address_id and last_address_id:
                address_id=last_address_id
                invoice_address_id=last_address_id if not invoice_address_id else invoice_address_id
            elif not address_id:
                address_id=rp_obj.id
                invoice_address_id=rp_obj.id if not invoice_address_id else invoice_address_id
            val={'address_id':address_id,'invoice_address_id':invoice_address_id}
        return {'value':val}
    
    AVAILABILITY_SELECTION = [('inused',"IN USE"),("cancelled","CANCELLED")]
    
    _columns={
                'revise_date': fields.date('Rev. Date'),
                'availability':fields.selection(AVAILABILITY_SELECTION,'Availability',readonly=True),
                'remark':fields.char('Remark',size=128)
              }
    _defaults={
               'availability':lambda *x: 'inused'
               }
kderp_contract_client()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

