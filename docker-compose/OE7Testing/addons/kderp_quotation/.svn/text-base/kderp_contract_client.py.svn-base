from openerp.osv.orm import Model
from openerp.osv import fields
import openerp.addons.decimal_precision as dp
import re

class kderp_contract_client(Model):
    _name='kderp.contract.client'    
    _inherit='kderp.contract.client'
    
    _columns={
              'quotation_ids':fields.one2many('sale.order','contract_id','Quotations',readonly=True),
              }
kderp_contract_client()