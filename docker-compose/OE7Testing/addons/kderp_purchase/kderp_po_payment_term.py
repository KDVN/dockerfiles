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
#    This program is distributed in the ho   pe that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import netsvc

from osv import fields, osv

from tools.misc import currency
from tools.translate import _
import pooler

from tools import config

class kderp_po_payment_term_line(osv.osv):
    _name = "kderp.po.payment.term.line"
    _description = "KDVN P.O. Payment Term Line"
    
    def _get_new_seq(self, cr, uid, context={}):
        from kderp_base import kderp_base
        if not context:
            context={}
        new_val = kderp_base.get_new_from_tree(cr, uid, context.get('id',False), self,context.get('term_lines',[]),'sequence', 0, 5, context)
        return new_val
    
    def _get_amount(self, cr, uid, ids, *args):
        res = {}
        for kptl in self.browse(cr, uid, ids):           
            
            po=kptl.order_id
            if kptl.type=='p':
                adv_amount = 0.0
                retention_amount = 0.0
                for po_term in po.purchase_payment_term_ids:
                    if po_term.type=='adv':
                        adv_amount += po_term.value_amount*po.final_price/100.0
                    elif po_term.type=='re':
                        retention_amount += po_term.value_amount*po.final_price/100.0                                                
                progress = po_term.value_amount
                
                this_progress_amount = po.final_price*po_term.value_amount/100.0
                this_adv_amount = - adv_amount*progress/100.0
                this_retention_amount = - retention_amount*progress/100.0
                
                this_tax_amount = po.amount_tax*kptl.value_amount/100.0
                
                sub_total= this_progress_amount + this_adv_amount + this_retention_amount + this_tax_amount
                
                res[kptl.id] = sub_total
            else:
                res[kptl.id] = kptl.value_amount*po.final_price/100.0
        return res
    
    def name_get(self, cr, uid, ids, context={}): # Return name + " - " + type
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name', 'type'], context)
        res = []
        for record in reads:
            payment_term_type=self.fields_get(cr,uid,'type')
            name = dict(payment_term_type['type']['selection'])[record['type']]            
            if record['name'] and name:
                name = record['name'] + ' - ' + name
            res.append((record['id'], name))
        return res
    
    _columns = {
        'name': fields.char('Description', size=100, required=True),
        'sequence': fields.integer('Sequence',required=True, help="The sequence field is used to order the payment term lines from the lowest sequences to the higher ones"),
        'type':fields.selection([('adv','Advanced'),('p','Progress'),('re','Retention')],'Type',required=True),
        'value_amount':fields.float('Percentage'),        
        'order_id':fields.many2one('purchase.order','Orders'),
        'due_date':fields.date('Due date'),
        'payment_amount':fields.function(_get_amount,type='float',method=True,string='Payment Amount')
    }
    _sql_constraints = [('value_amount_greater_0', 'check(value_amount>0 and value_amount<=100)', 'KDVN Error: The amount must be between 1 and 100!')]
    _defaults = {
        'name': lambda *a:'Progress',
        'sequence': _get_new_seq,
        'type':lambda *x:'p',
        'value_amount':lambda *a: 100.0
    }
    _order = "sequence"
kderp_po_payment_term_line()
