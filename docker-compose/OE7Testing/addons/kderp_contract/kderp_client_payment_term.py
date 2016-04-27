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
import time
import netsvc

from osv import fields, osv

from tools.misc import currency
from tools.translate import _
import pooler

from tools import config


class kderp_client_payment_term(osv.osv):
    _name = "kderp.client.payment.term"
    _description = "KDERP Client Payment Term"
    
    def _get_new_seq(self, cr, uid, context={}):
        from kderp_base import kderp_base
        if not context:
            context={}
        new_val = kderp_base.get_new_from_tree(cr, uid, context.get('id',False), self,context.get('term_lines',[]),'sequence', 0, 5, context)
        return new_val

    def search(self, cr, user, args, offset=0, limit=None, order=None,  context=None, count=False):
        if not context:
            context={}
        if context.get('contract_id',False):
                cr.execute("Select \
                                id \
                            from \
                                kderp_client_payment_term\
                            where \
                                contract_id=%s" % context['contract_id'])
                res = cr.fetchall()
                res1=[]
                for tmp in res:
                    res1.append(tmp[0])
                var_filter=res1
                args.append(('id','in',var_filter))
    #                return var_filter
                context=None
            #raise osv.except_osv(_('Invalid action !'),_('Cannot delete Request(s) which are in (%s) State1!' %args))

       # args.append
        return super(kderp_client_payment_term,self).search(cr, user, args, offset, limit, order=order,context=context, count= count)

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
    
    def onchange_checkinclude(self, cr, uid, ids,type, tax_include):
        value={}
        if type=='p' and tax_include:
            warning = {
                    'title': _('KDERP Warning !'),
                    'message': _('VAT Include only using for Advanced and Retention case.')}
            value={'value':{'tax_include':False},'warning':warning}
        return value

    _columns = {
                'name': fields.char('Description', size=100, required=True),
                'sequence': fields.integer('Sequence', required=True, help="The sequence field is used to order the payment term from the lowest sequences to the higher ones"),
                'type':fields.selection([('adv','Advance Payment'),('p','Progress'),('re','Retention')],'Type',required=True),
                'value': fields.selection([('percent', 'Percent'),('fixed', 'Fixed Amount')], 'Value',required=True),#('fixed', 'Fixed Amount')
                'value_amount':fields.float('Percentage', help="For Value percent enter % ratio between 0-1."),
                'due_date':fields.date('Due date'),
                'tax_include':fields.boolean('Included VAT'),        
                'contract_id':fields.many2one('kderp.contract.client','Contract',ondelete='restrict')
    }
    _defaults = {
        'value': lambda *a: 'percent',
        'sequence':_get_new_seq,
        'type':lambda *x:'p'
    }
    _order = "sequence,id"
kderp_client_payment_term()