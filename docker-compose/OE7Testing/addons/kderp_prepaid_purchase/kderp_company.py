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
             'location_code':fields.selection((('4','Hanoi'),('8','HCM')),'Location', help='Using for move code', required = True),
             }
    _defaults={
               'location_code':lambda self, cr, uid, context = {}: '8' if cr.dbname.count('HCM')>0 else '4' 
               }
res_company()