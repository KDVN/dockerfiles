# __init__.py
from openerp.osv import orm, fields


class Times(orm.Model):
    _name = 'kderp_oe_anatomy.stopwatch'

    _columns = {
        'time': fields.integer("Time", required=True,
                               help="Measured time in milliseconds"),
        'user_id': fields.many2one('res.users', "User", required=True,
                                   help="User who registered the measurement")
    }