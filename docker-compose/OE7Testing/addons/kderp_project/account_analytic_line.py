from openerp.osv import fields, osv

class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'
    _columns = {
                'amount_currency': fields.related('move_id', 'amount_currency', type='float', string='Amount Currency', store=True, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True)
                }
account_analytic_line()
        