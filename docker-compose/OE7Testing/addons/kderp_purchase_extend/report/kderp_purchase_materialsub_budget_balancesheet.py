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


import jasper_reports

from openerp.osv import fields, osv
from openerp import pooler

def kderp_material_sub_con_sheet(cr, uid, ids, data, context):
    if not context:
        context={}
    #Check if print from Purchase find Job IDs in Purchase
    if context.get('active_model','')=='purchase.order':
        job_ids=[]
        for po in pooler.get_pool(cr.dbname).get('purchase.order').browse(cr, uid, ids):
            for pol in po.order_line:
                job_ids.append(pol.account_analytic_id.id)
        job_ids=list(set(job_ids))
        ids=job_ids
                        
    return {'ids': ids,                        
            }
jasper_reports.report_jasper(
   'report.kderp.material.sub.con.sheet',
   'account.analytic.account',
   parser=kderp_material_sub_con_sheet
)

def kderp_material_sub_con_ex_sheet(cr, uid, ids, data, context):
    if not context:
        context={}
    #Check if print from Purchase find Job IDs in Purchase
    if context.get('active_model','')=='purchase.order':
        job_ids=[]
        for po in pooler.get_pool(cr.dbname).get('purchase.order').browse(cr, uid, ids):
            for pol in po.order_line:
                job_ids.append(pol.account_analytic_id.id)
        job_ids=list(set(job_ids))
        ids=job_ids
                        
    return {'ids': ids,                        
            }
jasper_reports.report_jasper(
   'report.kderp.material.sub.con.ex.sheet',
   'account.analytic.account',
   parser=kderp_material_sub_con_ex_sheet
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
