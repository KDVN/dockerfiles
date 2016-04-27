from osv import fields
from osv import osv

import netsvc
import pooler
import time
from osv.orm import browse_record

class wiz_contract_contract_client_report_open(osv.TransientModel):
    _name='test.project.open'
    def _open_contract_to_client_report(self, cr, uid, data, context):
        pool_obj = pooler.get_pool(cr.dbname)
        ctc_ids = ','.join(map(str,data['ids']))
        #quotation_ids = cr.fetchall()
        value = {
            'name': 'Contract to Client Report',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.account',
            'type': 'ir.actions.act_window',
        }
        return value

    states = {
        'init' : {
            'actions' : [],
            'result' : {'type':'action', 'action':_open_contract_to_client_report, 'state':'end'}
        }
    }
wiz_contract_contract_client_report_open()