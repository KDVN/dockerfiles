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
import openerp.addons.decimal_precision as dp

class account_invoice_line(osv.osv):

    _name = "account.invoice.line"
    _inherit="account.invoice.line"    

    def _total_amount_line(self, cr, uid, ids, name, args, context):
        context = context or {}
        res = {}
        for ail in self.browse(cr, uid, ids, context):
            res[ail.id] = ail.price_unit + ail.amount_tax
        return res


    def _price_amount_taxes_auto(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            if line.invoice_id.tax_base == 'p':
                compute_amount = line.amount * (1 - (line.discount or 0.0) / 100.0)
            elif line.invoice_id.tax_base == 'p_adv':
                compute_amount = line.advanced
            elif line.invoice_id.tax_base == 'p_retention':
                compute_amount = line.retention
            else:
                compute_amount = line.price_unit
            vat_per = 0
            for kcr in line.invoice_id.contract_id.contract_summary_currency_ids:
                vat_per = 100 * (kcr.tax_amount / kcr.amount) if kcr.amount else 0
                break

            vat_per = int(vat_per)
            if vat_per in (4,6):
                vat_per = 5
            elif vat_per in (9,11):
                vat_per = 10

            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, compute_amount, 1, False,
                                        partner=line.invoice_id.partner_id)
            res[line.id] = compute_amount * vat_per / 100.0

        return res

    _columns={
                'amount_taxes_auto':fields.function(_price_amount_taxes_auto, string='VAT (Auto)', type="float", digits_compute=dp.get_precision('Amount')),
                'job_code':fields.related('account_analytic_id','code',string='Job Code',type='char',size=16,store=True),
                'total_amount_line':fields.function(_total_amount_line, string='Sub-Total', type="float", digits_compute=dp.get_precision('Amount'))
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