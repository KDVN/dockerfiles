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
    _description = 'Attachment'
  
    #Quotation Budget
    def onchange_quotation_buget_na(self, cr, uid, ids,quotation_budget_na=False, q_attached_qcombine=False,q_attached_bm=False,q_attached_be=False):
        value={}
        if quotation_budget_na==True:
            value={'value':{'q_attached_qcombine':False,'q_attached_be':False,'q_attached_bm':False}}
        return value
            
    def onchange_quotation_buget(self, cr, uid, ids,quotation_budget_na=False, q_attached_qcombine=False,q_attached_bm=False,q_attached_be=False):
        value={}
        if q_attached_qcombine==True or q_attached_bm==True or q_attached_be==True:
                value={'value':{'quotation_budget_na':False}}
        return value
    
#     #Quotation
#     def onchange_quotation_na(self, cr, uid, ids,quotation_na):
#         value={}
#         if quotation_na==True:
#             value={'value':{'q_attached':False}}
#         return value
#             
#     def onchange_quotation(self, cr, uid, ids, q_attached=False):
#         value={}
#         if q_attached:
#                 value={'value':{'quotation_na':False}}
#         return value
    
    #Quotation Job Budget
    def onchange_quotation_job_budget_na(self, cr, uid, ids,quotation_job_budget_na=False):
        value={}
        if quotation_job_budget_na:
            value={'value':{'q_attached_je':False,
                            'q_attached_jm':False,
                            'q_attached_jcombine':False}}
        return value
            
    def onchange_quotation_job_budget(self, cr, uid, ids, q_attached_je=False, q_attached_jm=False, q_attached_jcombine=False):
        value={}
        if q_attached_je or q_attached_jm or q_attached_jcombine:
                value={'value':{'quotation_job_budget_na':False}}
        return value
    
    _columns = {
                    'quotation_budget_na':fields.boolean('N/A'),
                    #'quotation_na':fields.boolean('N/A'),
                    'quotation_job_budget_na':fields.boolean('N/A'),
               }
ir_attachment()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

