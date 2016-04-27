import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class kderp_quotation_contract_project_line(osv.osv):
    _name='kderp.quotation.contract.project.line'
    _description='KDERP Quotation Contract Project Line'
    _rec_name='account_analytic_id'
    
    def check_update_and_create(self, cr, uid, contract_id, job_id, currency_id):
        filter ='contract_id = %d and job_e_id=%d and currency_id=%d' % (contract_id,job_id,currency_id)
        filter2 ='contract_id = %d and job_m_id=%d and currency_id=%d' % (contract_id,job_id,currency_id)
        filter3 ='contract_id = %d and account_analytic_id=%d and currency_id=%d' % (contract_id,job_id,currency_id)

        cr.execute("""Select 
                        contract_id,
                        job_e_id as job_id,
                        currency_id 
                    from 
                        sale_order so left join sale_order_line sol on so.id = sol.order_id  and job_type='E'
                    where
                        so.state='done' and %s
                    Union
                    Select 
                        contract_id,
                        job_m_id as job_id,
                        currency_id 
                    from 
                        sale_order so left join sale_order_line sol on so.id = sol.order_id and job_type='M'
                    where
                        so.state='done' and %s""" % (filter,filter2))
        if cr.fetchall():
            cr.execute("""Select
                            sum(amount) as amount
                        from
                            (Select 
                               sum(coalesce(sol.price_unit,0)+coalesce(sol.discount,0)) as amount
                            from 
                                sale_order so left join sale_order_line sol on so.id = sol.order_id and job_type='E' 
                            where
                                so.state='done' and
                                %s
                            Group by 
                                contract_id,
                                job_e_id,
                                currency_id
                            Union
                            Select 
                              sum(coalesce(sol.price_unit,0)+coalesce(sol.discount,0)) as amount    
                            from 
                                sale_order so left join sale_order_line sol on so.id = sol.order_id and job_type='M'
                            where
                                so.state='done' and
                                %s
                            Group by 
                                contract_id,
                                job_m_id,
                                currency_id) vwtest""" % (filter,filter2))
            amt = cr.fetchone()[0]
            
            cr.execute("""Select id from kderp_quotation_contract_project_line where %s""" % filter3)
            if cr.fetchall():
                #cr.execute("Update kderp_quotation_contract_project_line set amount_currency=%s where %s" % (amt,filter3))
                cr.execute("""select id from kderp_quotation_contract_project_line where %s""" % (filter3))
                for id in cr.fetchall():
                    result = self.write(cr,uid,id[0],{'amount_currency':amt})
            else:
                new_id = self.create(cr,uid,{'amount_currency':amt,'contract_id':contract_id,'account_analytic_id':job_id,'currency_id':currency_id})
                return new_id
        else:
            cr.execute("""Select id from kderp_quotation_contract_project_line where contract_id=%d and account_analytic_id=%d and currency_id=%d""" %(contract_id,job_id,currency_id))
            for id in cr.fetchall():
                result = self.unlink(cr,uid,id[0])
            #cr.execute("Delete from kderp_quotation_contract_project_line where contract_id=%d and account_analytic_id=%d and currency_id=%d" %(contract_id,job_id,currency_id))
        return False
       
    _columns={              
              'contract_id':fields.many2one('kderp.contract.client',"Contract",required=True,select=1),
              'account_analytic_id':fields.many2one('account.analytic.account','Job',required=True,select=1),
              'currency_id':fields.many2one('res.currency','Currency',required=True,select=1),
              'amount_currency': fields.float('Amount Currency', digits_compute=dp.get_precision('Amount')),
              }
    _defaults={
               'amount_currency':lambda *a:0.0
               }
    _sql_constraints = [('kderp_job_contract_unique', 'unique(contract_id,account_analytic_id,currency_id)', 'KDERP Error: The Contract, Job & Currency must be unique!')]
kderp_quotation_contract_project_line()