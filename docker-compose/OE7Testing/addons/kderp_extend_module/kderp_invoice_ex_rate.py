from osv import osv, fields

class kderp_payment_vat_invoice(osv.osv):
    """Using inherit add a column diff_rate to Client Payment VAT Invoice Allotment"""
    
    _name = 'kderp.payment.vat.invoice'
    _description = 'KDERP Payment VAT Invoice'
    _inherit= 'kderp.payment.vat.invoice'      
    
    _columns={
              'diff_exrate':fields.float('Ex.rate differences')
              }
kderp_payment_vat_invoice()
