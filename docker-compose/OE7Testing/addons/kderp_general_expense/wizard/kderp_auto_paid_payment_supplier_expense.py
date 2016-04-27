# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
from openerp.osv import osv
import logging
_logger = logging.getLogger(__name__)

class kderp_paid_supplier_other_expense(osv.osv_memory):
    """Create a memory Object for Update Paid to Supplier Payment Other Expense in case prepaid without VAT Invoice"""
    _name = "kderp.paid.supplier.other.expense"
    _description = "KDERP Cash Payment Supplier"
    
    def update_paid_other_payment_supplier(self, cr, uid, ids, cron_mode=True, context=None):
        #Update Supplier Payment Expense    

        cr.execute("""Select 
                        kspe.id as kspe_id,
                        kspe.date,
                        total,
                        kspe.currency_id,
                        kspe.exrate                        
                    from 
                        kderp_supplier_payment_expense kspe
                    left join
                        kderp_supplier_payment_expense_pay kspep on kspe.id = kspep.supplier_payment_expense_id
                    left join
                        kderp_other_expense koe on kspe.expense_id = koe.id
                    where 
                        kspe.state = 'completed' and
                        koe.state not in ('draft','cancel') and
                        coalesce(kspep.id,0)=0 and
                        koe.paid_auto""" )
        
        kpe_obj=self.pool.get('kderp.supplier.payment.expense.pay')
        kp_obj=self.pool.get('kderp.supplier.payment.pay')
       
        for ksp_id,date,amount,currency,exrate in cr.fetchall():
            try:
                kpe_obj.create(cr, uid, {'supplier_payment_expense_id':ksp_id,
                                          'amount':amount,
                                          'currency_id':currency,
                                          'exrate':exrate,
                                          'date':date},
                                          context)
                cr.commit()
            except ValueError, e:
                import time
                _logger.info("Error ON Update Auto Paid Supplier Payment Expense - Cash (%s) @ %s" % (e,time.strftime("%Y-%m-%d %H:%M")))
                cr.rollback()
                
        return True