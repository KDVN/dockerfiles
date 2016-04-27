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
from openerp.tools.translate import _
class quotation_job_select(osv.osv_memory):
    _name = "quotation.job.select"
    
    
    def _get_order_id(self,cr,uid,context={}):
        return context.get('order_id',False)
    _columns = {
                'order_id':fields.many2one('sale.order','order id',readonly=1),
                
               }
    _defaults={
               'order_id':_get_order_id
               }
    def action_open_window(self, cr, uid, ids, context=None):
        """
       @param cr: the current row, from the database cursor,
       @param uid: the current user’s ID for security checks,
       @param ids: account move bank reconcile’s ID or list of IDs
       @return: dictionary of  Open  account move line   on given journal_id.
        """
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        cr.execute('(Select\
                       job_e_id as id\
                    from \
                        sale_order\
                    where job_e_id is not null and id in (%s))\
                    Union\
                    (Select\
                        job_m_id as id\
                    from \
                        sale_order\
                    where job_m_id is not null and id in (%s))', (data['order_id'],))
        job_id = cr.fetchone()[0]
        if not job_id:
            raise osv.except_osv(_('Error!'), _('You have to define the bank account\
            nin the journal definition for reconciliation.'))
        return {
            'domain': "[ ('id,'in',%d)]" % (data['order_id']),
                        'name': _('Standard Encoding'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.account',
            'view_id': False,
            'context': "{'id': %d}" % (data['order_id'],),
            'type': 'ir.actions.act_window'
             }

    
quotation_job_select()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
