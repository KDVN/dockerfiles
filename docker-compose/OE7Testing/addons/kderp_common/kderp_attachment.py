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

from osv import fields,osv
from osv.orm import except_orm
from openerp import pooler
import tools
import base64

class ir_attachment(osv.osv):
    _name = 'ir.attachment'
    _inherit ="ir.attachment"  
    
    def _get_res_id(self,cr,uid,context={}):
        return context.get('res_id',False)
    
    def _get_res_model(self,cr,uid,context={}):
        return context.get('res_model',False)
    
    def _get_type(self,cr, uid,ctx):
        ctx={}
        return 'binary'
    
    _columns = {
        #Cho Quotation Attachment
        'q_attached':fields.boolean('Quotation Attached'),
        'q_attached_be':fields.boolean('Quotation Budget E Attached'),
        'q_attached_bm':fields.boolean('Quotation Budget M Attached'),
        'q_attached_qcombine':fields.boolean('Q.Budget Combine'),
        'q_attached_je':fields.boolean('Quotation Job Budget E Attached'),
        'q_attached_jm':fields.boolean('Quotation Job Budget M Attached'),
        'q_attached_jcombine':fields.boolean('J.Budget Combine'),
        #'quotation_budget_no':fields.boolean('N/A'),
        #Contract Attachment
        'attached_contract_sent':fields.boolean('Contract Sent'),
        'attached_contract_received':fields.boolean('Contract Received'),
        #Client Payment Attachment
        'attached_progress_sent':fields.boolean("Progress Sent"),
        'attached_progress_received':fields.boolean("Progress Received"),
        'attached_approved_quotation':fields.boolean("Approved Quotation"),
        #Purchase Order Attachment
        'quotation_attached':fields.boolean("Quotation"),
        'roa_comaprison_attached':fields.boolean("ROA/Comparison Sheet"),
        'contract_attached':fields.boolean("Contract"),
        
        'res_model': fields.char('Attached Model', size=64), #res_model
        'res_id': fields.integer('Attached ID'), #res_id
        'type': fields.selection( [ ('url','URL'), ('binary','Binary'), ],
                'Type', help="Binary File or URL", required=True),
    }
    
    _defaults={
            'type':_get_type,
            'res_id':_get_res_id,
            'res_model':_get_res_model,
            'q_attached':lambda *a:False,
            'q_attached_be':lambda *a:False,
            'q_attached_bm':lambda *a:False,
            'q_attached_qcombine':lambda *a:False,
            'q_attached_je':lambda *a:False,
            'q_attached_jm':lambda *a:False,
            'q_attached_jcombine':lambda *a:False, 
            #'quotation_budget_no':lambda *a:False,   
            'attached_contract_sent':lambda *a:False,
            'attached_contract_received':lambda *a:False,
            'attached_approved_quotation':lambda *a:False,
            'attached_progress_sent':lambda *a:False,
            'attached_progress_received':lambda *a:False,
            'quotation_attached':lambda *a:False,
            'roa_comaprison_attached':lambda *a:False,
            'contract_attached':lambda *a:False,
            }
    
    def onchange_name(self, cr, uid, ids,name):
        if name:
            val={'value':{'name':name}}
        else:
            val={}
        return val
    
    def onchange_type(self,cr,uid,ids,type):
        if type !='URL' :
            val={'value':{'type':'binary'}}
        else:
            val={'value':{'type':'URL'}}
        return val
    
    def check_location(self, cr, uid, unused_param, context=None):
        location = self.pool.get('res.users').read(cr, uid, [uid], ['location_user'])[0]['location_user']
        return location
        
    def has_gorup_hidden(self, cr, uid, unused_param, context=None):
        try:
            model, group_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'kderp_common', 'group_kderp_hidden_attachment')
        except ValueError:
            return False
        return group_id in self.pool.get('res.users').read(cr, uid, uid, ['groups_id'], context=context)['groups_id']

ir_attachment()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

