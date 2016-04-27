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
import openerp.addons.decimal_precision as dp

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    _description = 'Analytic Account'

    JOB_SCALE_SELECTION = [('00-big_job','Big Job'), ('01-small_maintenance', 'Small/Maintenance Job'), ('02-f-cost','F-Cost Job')]
    def _get_job_scale(self, cr, uid, ids, name, args, context = {}):
        res = {}
        #Them 00, 01, 02 dung cho sap xep trong bao cao
        for job in self.browse(cr, uid, ids):
            jobCode = job.code.upper()
            if jobCode[1:2] == 'A' or len(jobCode)<9: #Trong truong hop Job la HA hoac Code ko dung dinh dang
                res[job.id] = False
            elif len(jobCode)>10 and jobCode[10:11] == 'F':
                res[job.id] = '02-f-cost'
            elif jobCode[4:6] == '-0':
                res[job.id] = '00-big_job'
            elif jobCode[4:6] in ('-1','-2'):
                res[job.id] = '01-small_maintenance'
        return res

    def _get_vat_issued_amount_custom(self, cr, uid, ids, name, args, context = {}):
        context = context or {}
        res = {}
        from_date = context.get('from_date', False)
        to_date = context.get('to_date', False)
        if from_date and not to_date:
            from datetime import date
            to_date = date(date.today().year, 12, 31).strftime("%Y-%m-%d")
        elif to_date and not from_date:
            from datetime import date
            from_date = date(1900, 1, 1).strftime("%Y-%m-%d")
        if to_date and from_date:
            sqlCommand = """Select
                                  job_id,
                                  coalesce(issued_amount,0)
                            from
                              account_analytic_account aaa
                            left join
                                funjobvatissued('%s', '%s', array %s) vwtemp on aaa.id = vwtemp.job_id
                            WHERE
                                aaa.id in (%s)""" % (from_date, to_date, ids, ",".join(map(str, ids)))
            cr.execute(sqlCommand)
            for id, amount in cr.fetchall():
                res[id] = amount
        else:
            for job in self.browse(cr, uid, ids, context):
                res[job.id] = job.vat_issued_subtotal
        return res

    _columns={
                # 'control_area_id':fields.many2one('kderp.control.area','Control Area', ondelete='restrict'),

                # 'support_area_id': fields.many2one('kderp.control.area','Support Area', ondelete='restrict'),

                #'target_profit': fields.float('Target Profit', digits_compute=dp.get_precision('Amount')),
                'target_profit': fields.char('Targeted Gross Profit', size=6),
                'kickoff_meeting_date': fields.date('K.O.M. Date', help="Kick-off meeting Date"),

                # FIXME Truong nay se co ten la Job Type, Job Type doi thanh E/M, phai hop nhat khi Upgrade len Odoo
                'job_scale':fields.function(_get_job_scale, type = 'selection', string = 'Job Type', selection = JOB_SCALE_SELECTION, method = True, select = 1,
                                            store = {'account.analytic.account':(lambda self, cr, uid, ids, context = {}: ids, ['code'], 50),}),

                'control_area_ids':fields.one2many('kderp.job.control.area', 'job_id', 'Control Area'),
                'area_allotment_ids': fields.one2many('kderp.job.area.allotment', 'job_id', 'Area Allotment', readonly=1),

                'vat_issued_subtotal_custom':fields.function(_get_vat_issued_amount_custom, type='float', method=True, string='VAT Issued Amount', digits_compute=dp.get_precision('Amount'))
              }

    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        context = context or {}
        if context.get("filter_by_contract_id", False):
            contract_id = context.get("filter_by_contract_id", False)
            sqlConn = """Select DISTINCT account_analytic_id from kderp_quotation_contract_project_line kqcpl where contract_id=%s""" % contract_id
            cr.execute(sqlConn)
            job_ids = [job_id[0] for job_id in cr.fetchall()]
            args.append(('id','in',job_ids))
        return super(account_analytic_account, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=False)

    def init(self, cr):
        #Function using for Get Issued VAT Amount (range date)
        sqlCommand="""CREATE OR REPLACE FUNCTION funjobvatissued(
                            IN fromdate date,
                            IN todate date,
                            IN ids integer[])
                          RETURNS TABLE(job_id integer, issued_amount double precision) AS
                        $BODY$
                        BEGIN
                            RETURN QUERY
                            Select
                                aaa.id as job_id,
                                sum(coalesce(issued_subtotal,0)* case when coalesce(total,0)=0 then 0 else coalesce(amount_currency,0)/total end) as vat_issued_subtotal
                            from
                                account_analytic_account aaa
                            left join
                                kderp_quotation_contract_project_line kqcpl on aaa.id = account_analytic_id
                            left join
                                (select
                                    contract_id,
                                    sum(coalesce(amount_currency,0)) as total
                                from
                                    kderp_quotation_contract_project_line kqcpls
                                where
                                    contract_id in (select distinct contract_id from kderp_quotation_contract_project_line kqcpls where kqcpls.account_analytic_id = any(ids))
                                group by
                                    contract_id) astemp on  kqcpl.contract_id = astemp.contract_id
                            left join
                                account_invoice ai on kqcpl.contract_id = ai.contract_id
                            left join
                                (Select
                                    payment_id,
                                    sum(kpvi.amount/(1+coalesce(tax_percent,0)/100)) as issued_subtotal,
                                    sum(case when coalesce(tax_percent,0)=0 then 0 else  kpvi.amount/(1+coalesce(tax_percent,0)/100)/tax_percent end) as issued_vat
                                from
                                    kderp_payment_vat_invoice kpvi
                                left join
                                    kderp_invoice ki on vat_invoice_id=ki.id
                                where
                                    ki.date BETWEEN fromDate
                                        AND toDate
                                group by
                                    payment_id) vwpayment_vat on ai.id=vwpayment_vat.payment_id and coalesce(vwpayment_vat.payment_id,0)>0
                                where
                                    aaa.id =any(ids)
                                group by
                                    aaa.id;
                            END;
                            $BODY$
                              LANGUAGE plpgsql VOLATILE
                              COST 100
                              ROWS 1000;"""
        cr.execute(sqlCommand)
account_analytic_account()