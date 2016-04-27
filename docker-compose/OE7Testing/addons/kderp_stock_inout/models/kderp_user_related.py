__author__ = 'tnd34'

from openerp.osv import osv, fields

class UserRelated(osv.osv):
    """
        Store name of user related such as User received product (Subcontractor or Customer)
    """
    _name = 'kderp.user.related'

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        }
    _sql_constraints = [('userrelated_unique_name','unique(name)','Name in User Related must be unique')]
