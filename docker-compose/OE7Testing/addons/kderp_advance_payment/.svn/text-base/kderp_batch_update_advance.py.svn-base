import time

from openerp.osv import fields, osv
from openerp import netsvc
from openerp import pooler


class kderp_batch_update_advance(osv.osv):
    _name = 'kderp.batch.update.advance'
    _description = 'KDERP Batch Update Advance Payment for Kinden'
    _order='name desc'
    
    STATE_SELECTION = [('draft','Processing'), #Meaning Inputting data                     
                     ('done','Updated')]
    
    def kua_clear(self, cr, uid, ids, context={}):
        for kbua_obj in self.browse(cr, uid, ids):
            for kap in kbua_obj.kbua_advance_ids:            
                self.write(cr, uid, ids,{'kbua_advance_ids':[(3,kap.id)]})
        return True
    
    def kua_submit(self, cr, uid, ids, context={}):
        kap_obj=self.pool.get('kderp.advance.payment')
        wf_service = netsvc.LocalService("workflow")
        
        for kbua_obj in self.browse(cr, uid, ids, context):
            kap_ids=[]
            for kap in kbua_obj.kbua_advance_ids:
                kap_ids.append(kap.id)
            vals={}
            done=False
            if kbua_obj.date_acc_recv_doc:
                done=True
                vals.update({'date_acc_recv_doc':kbua_obj.date_acc_recv_doc})
            if kbua_obj.date_acc_recv_cashbook:
                done=True
                vals.update({'date_acc_recv_cashbook':kbua_obj.date_acc_recv_cashbook})
            kap_obj.write(cr, uid, kap_ids,vals)
            kap_done_ids=[]
            for kap in kbua_obj.kbua_advance_ids:                
                if kap.state=='waiting_for_complete' and kap.date_acc_recv_cashbook and kap.advance_buying!='cash':
                    kap_obj.write(cr, uid, [kap.id],{'state':'done'})                            
                    wf_service.trg_delete(uid, 'kderp.advance.payment', kap.id, cr)
            if done:
                self.write(cr, uid, kbua_obj.id,{'state':'done'})
        return True
    
    _columns={
              'name':fields.char('Code Import',size=32,required=True,select=True,states={'done':[('readonly',True)]}),
              'state':fields.selection(STATE_SELECTION,'State',readonly=True),
              'date_acc_recv_doc':fields.date('Receive Request Adv.',states={'done':[('readonly',True)]}),
              'date_acc_recv_cashbook':fields.date('Receive CashBook',states={'done':[('readonly',True)]}),
              'kbua_advance_ids':fields.many2many('kderp.advance.payment','kderp_bua_advance_m2m','kbua_id','adv_id','List of Advance',states={'done':[('readonly',True)]})                                                
              }
    
    _sql_constraints = [
                        ('adv_import_unique',"unique(name)","KDERP Error: The Code Import must be unique !")
                        ]
    _defaults={
               'name':lambda *a: time.strftime('AUADV-%Y%b%d.%H%M'),
               'state': 'draft'
               }
kderp_batch_update_advance()