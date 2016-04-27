import re
import time

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_round, float_is_zero, float_compare
from openerp.tools.translate import _

class res_users(osv.osv):
    _name = "res.users"
    _description = "Users"
    _inherit = "res.users"
    _columns={
              "location_user":fields.selection([('all','Global'),('hanoi','Ha Noi Office'),('hcm','Ho Chi Minh Office'),('haiphong','Hai Phong Office')],'Location',select=1)
              }
res_users()