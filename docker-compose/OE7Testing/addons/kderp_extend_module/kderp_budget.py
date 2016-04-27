from osv import osv, fields

class account_buget_post(osv.osv):
    """
        Inherit Budget Code
    """
    _name = 'account.budget.post'
    _inherit = 'account.budget.post'
    _description="Budget"    
    
    _columns={                      
         'active': fields.boolean("Active")
         }
    _defaults  ={            
        'active': True
            }