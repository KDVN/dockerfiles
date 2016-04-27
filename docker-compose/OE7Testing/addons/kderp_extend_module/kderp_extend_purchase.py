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
import time

class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'Purchase Order'
    
    def _get_address_project_location(self, cr, uid, ids, name, args, context=None):
        res = {}
        if ids:
            po_ids = ",".join(map(str,ids))
            cr.execute("""select po.id as id , kpl.id  from 
                            purchase_order po 
                            left join kderp_project_location kpl 
                            on kpl.account_analytic_id=po.account_analytic_id
                            where po.id in (%s)
                               """ % (po_ids))
            for id,delivery_location_id in cr.fetchall():
                res[id]=delivery_location_id
        return res
    
    #Thay doi Date Order theo Revision No
    def onchange_revision_date(self, cr, uid, ids, revision_no):
        value={}
        if ids:
            for po in self.browse(cr, uid, ids, context=None):
                if po.revision_no != revision_no :
                    date_order = time.strftime('%Y-%m-%d')
                else :
                    date_order = po.date_order
            value = {'date_order':date_order}
        return {'value':value}
    
    _columns={
                'revision_no':fields.integer('Revision No.',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),
                'receiver_id': fields.many2one('hr.employee', 'Receiver', select=1,ondelete='restrict'),
                #'general_contract_no':fields.char('G.C. No.',size=16),
                #'general_contract_date':fields.date('G.C. Date'),
                #'delivery_location_id':fields.function(_get_address_project_location, type='many2one', relation='kderp.project.location',method=True,string='Delivery Location'),
                'delivery_location_id':fields.many2one('kderp.project.location','Delivery Location',states={'done':[('readonly',True)], 'cancel':[('readonly',True)]}),                                
             }
    
    _defaults={
               'revision_no':lambda *x:0,              
               }
    
purchase_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

