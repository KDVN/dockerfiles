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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'
    
    _columns={
                'state': fields.selection([('doing','On-Going'),('done','Completed'),('closed','Closed'),('cancel','Cancelled')], "Prj. Status",required=True,select=1, track_visibility='onchange'),
                'process_status':fields.selection([('doing','On-Going'),('done','Completed'),('closed','Closed'),('cancel','Cancelled')],"Process Status",select=1),
                #Them truong moi
                'remark':fields.text('Remark'),
              }

    def onchange_job_code(self, cr, uid, ids, code):
        value = {}
        if code:
            code = code.replace(' ', '')
            job_type = code[1:2]
            value = {'job_type': job_type}
        return {'value':value}
    
    def onchange_job_type(self, cr, uid, ids, code, job_type):
        if code:
            if code[1:2] != job_type:
               return {'value':{}, 'warning':{'title':'KDERP Warning','message':'Check Job Code'}}
        return {'warning':{}}
      
    _sql_constraints = [('mask_code_analytic_account', "CHECK (code not ilike '% %')",  'Please check Job Code')]
account_analytic_account()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

