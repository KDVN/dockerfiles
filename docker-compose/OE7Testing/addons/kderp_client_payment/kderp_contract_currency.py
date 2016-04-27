import operator
import time

from osv import osv, fields
from osv.orm import intersect

import openerp.addons.decimal_precision as dp

import tools.sql
from tools import config
from tools.translate import _

import netsvc
import datetime

from openerp.tools import float_round

class kderp_contract_currency(osv.osv):
    _name = 'kderp.contract.currency'
    _inherit = 'kderp.contract.currency'
    _desciption = "KDERP Currency System for Contract"
    
    def _get_contract_currency_summary_info(self, cr, uid, ids, name, arg, context=None):
        res = {}
       
        for ctcc in self.browse(cr,uid,ids):
            claimed_amount = 0.0
            collect_amount = 0.0

            for inv in ctcc.contract_id.client_payment_ids:
                if inv.state not in ('cancel','draft') and inv.currency_id.id==ctcc.name.id:                    
                    claimed_amount+=inv.amount_untaxed
                    if inv.state=='paid':
                        collect_amount+=inv.amount_untaxed

            res[ctcc.id] = {
                            'claimed_amount':claimed_amount,
                            'collect_amount':collect_amount
                            }
        return res
    
    def _get_contract_currency_contract(self, cr, uid, ids, context=None):
        res={}
        for ctc in self.browse(cr,uid,ids):
            for ctcc in ctc.contract_summary_currency_ids:
                res[ctcc.id] = True
        return res.keys()
    
    def _get_contract_invoice(self, cr, uid, ids, context=None):
        res={}
        for inv in self.browse(cr,uid,ids):
            for ctcc in inv.contract_id.contract_summary_currency_ids:
                res[ctcc.id] = True
        return res.keys()
        
    _columns = {
                'claimed_amount':fields.function(_get_contract_currency_summary_info,type='float',digits_compute=dp.get_precision('Amount'), method=True,string='Claimed',multi='get_summary_contract_info',
                                             store={
                                                    'kderp.contract.currency':(lambda self, cr, uid, ids, c={}: ids, None, 30),
                                                    'kderp.contract.client':(_get_contract_currency_contract,['contract_currency_ids','contract_summary_currency_ids'],35),
                                                    'account.invoice':(_get_contract_invoice,['state','invoice_line','currency_id','journal_id','contract_id'],35)}),
                'collect_amount':fields.function(_get_contract_currency_summary_info,type='float',
                                                 digits_compute=dp.get_precision('Amount'), method=True,string='Received',
                                                 multi='get_summary_contract_info',
                                                 store={
                                                        'kderp.contract.currency':(lambda self, cr, uid, ids, c={}: ids, None, 30),
                                                        'kderp.contract.client':(_get_contract_currency_contract, ['contract_currency_ids','contract_summary_currency_ids'],35),
                                                        'account.invoice':(_get_contract_invoice,['state','invoice_line','currency_id','journal_id','contract_id'],35)}),
                }
    _defaults = {}
    
kderp_contract_currency()