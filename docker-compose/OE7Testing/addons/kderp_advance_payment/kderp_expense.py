import time
from datetime import datetime
from openerp.osv.orm import Model
from openerp.osv import fields, osv

import openerp.addons.decimal_precision as dp
import re

class purchase_order(Model):
    _inherit='purchase.order'
    _description='Add Advance Relation to PO'
    
    _columns={
              'advance_payment_id':fields.many2one('kderp.advance.payment','Advance',domain=[('state','not in',('draft','cancel'))])
              }
purchase_order()

class kderp_other_expense(Model):
    _inherit='kderp.other.expense'
    _description='Add Advance Relation to Other Expense'
    
    _columns={
              'advance_payment_id':fields.many2one('kderp.advance.payment','Advance',domain=[('state','not in',('draft','cancel'))])
              }
kderp_other_expense()