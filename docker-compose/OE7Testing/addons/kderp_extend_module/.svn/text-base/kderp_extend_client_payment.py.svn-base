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

class account_invoice_line(osv.osv):

    _name = "account.invoice.line"
    _inherit="account.invoice.line"    
    
    _columns={
              'job_code':fields.related('account_analytic_id','code',string='Job Code',type='char',size=16,store=True),
            }
    
    _order="job_code asc"
account_invoice_line()

class account_invoice(osv.osv):    
    """Add two fields P.E.S Send and Received"""
    
    _name = 'account.invoice'
    _description = 'KDERP Client Payment '
    _inherit= 'account.invoice'
    _columns={
              'pes_not_available':fields.boolean('P.E.S. N/A'),
              'pes_cannot_collect':fields.boolean("P.E.S. Can't Collect")
              }
    #Add new SQL Constraint Check Check Attachment Info (Can't check PES Not Available and (PES Sent or Received) 
    #                                                                PES Cannot Collect and PES Received
    _sql_constraints=[('kderp_clp_attach_pes_sent_received',"""CHECK (
                                                            (not 
                                                                (coalesce(pes_not_available,false) and 
                                                                (coalesce(attached_progress_sent,false) or coalesce(attached_progress_received,False))
                                                            ))
                                                            and
                                                            (not 
                                                                (coalesce(pes_cannot_collect,false) and coalesce(attached_progress_received,False))
                                                            )
                                                            )""",'Please check your input data P.E.S. !')]
    
account_invoice()