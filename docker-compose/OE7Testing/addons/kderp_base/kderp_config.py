import re
import time

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_round, float_is_zero, float_compare
from openerp.tools.translate import _

class res_company(osv.osv):
    _inherit = 'res.company'
    _name = 'res.company'
    
    _columns={
             'over_budget_value':fields.float("Balance Over Budget",help='Amount of Calculate Over Budget Balance'),
             }
    _defaults={
               'over_budget_value':lambda *x:0.0
               }
res_company()

class kderp_config(osv.osv):
    _name = "kderp.config"
    _description = "KDERP Config"

    TYPE_SELECTION=[('over_budget','Over Budget'),
                   ('domain_filter','Domain Filter')]
    _columns={
              "type":fields.selection(TYPE_SELECTION,'Type',required=True),
              "model_id":fields.many2one('ir.model','Model',required=True),
              "domain":fields.text('Domain'),
              'value':fields.float('Value')
              }
    _defaults={
               'value':lambda *x:0.0
               }
kderp_config()