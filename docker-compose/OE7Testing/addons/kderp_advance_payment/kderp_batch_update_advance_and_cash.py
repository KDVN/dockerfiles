import time

from openerp.osv import fields, osv

class kderp_batch_update_advance_and_cash(osv.osv):
    _name = 'kderp.batch.update.advance.and.cash'
    _description = 'KDERP Batch Update Advance and Cash for Kinden'
    _order='name desc'
    
    STATE_SELECTION = [('draft','Processing'), ('done','Updated')]

    def kpi_submit(self, cr, uid, ids, context={}):
        #Update Supplier Payment Expense
        cr.execute("""Select
                        kap.id,
                        date_receive_adv,
                        date_receivecashbook
                    from
                        kderp_advance_payment kap
                    inner join
                        (select
                            kdca.name,
                            min(kiaacl.date_acc_recv_adv) as date_receive_adv,
                            max(kiaacl.date_acc_recv_cash) as date_receivecashbook
                        from
                            kderp_import_advance_and_cash_line kiaacl
                        inner join
                            kderp_detail_cash_advance kdca on paymentno = voucher_no
                        where
                            kiaacl.payment_import_id in (%s)
                        Group by
                            kdca.name) vwtemp on kap.name = vwtemp.name"""  % (",".join(map(str,ids))))
        kap_obj = self.pool.get('kderp.advance.payment')
        for adv_id,date_receive_adv,date_receivecashbook in cr.fetchall():
            vals = {}
            if date_receive_adv:
                vals['date_acc_recv_doc'] = date_receive_adv
            if date_receivecashbook:
                vals['date_acc_recv_cashbook'] = date_receivecashbook
            kap_obj.write(cr, uid, [adv_id], vals)
        self.write(cr, uid, ids, {'state':'done'})
        return True

    _columns={
              'name':fields.char('Code Import',size=32,required=True,select=True,states={'done':[('readonly',True)]}),
              'date':fields.date('Date', required=True, states={'done':[('readonly',True)]}),
              'description':fields.char('Desc.',size=128,states={'done':[('readonly',True)]}),
              'state':fields.selection(STATE_SELECTION,'State',readonly=True),
              'kbua_advance_ids':fields.one2many('kderp.import.advance.and.cash.line','payment_import_id','Details',states={'done':[('readonly',True)]}),
              }
    
    _sql_constraints = [
                        ('adv_import_unique',"unique(name)","KDERP Error: The Code Import must be unique !")
                        ]
    _defaults={
               'name':lambda *a: time.strftime('AUADV-%Y%b%d.%H%M'),
               'date': lambda *a: time.strftime('%Y-%m-%d'),
               'state': 'draft'
               }

    def load(self, cr, uid, fields, data, context=None):
        try:
            payment_id_pos = fields.index('kbua_advance_ids/paymentno')
        except:
            payment_id_pos = -1

        data=list(set(data))

        voucherno_list =[]
        if payment_id_pos>=0:
            for pos in range(len(data)):
                if data[pos][payment_id_pos].upper().find('PC')>=0 or data[pos][payment_id_pos].upper().find('PT')>=0:
                    voucherno_list.append(str(data[pos][payment_id_pos]))
            payment_nos =str(voucherno_list if voucherno_list else "['false']" ).replace("[","(").replace("]",")")
#             raise osv.except_osv("KDVN Error",new_data)
            cr.execute("""Select
                            voucher_no
                          from
                              kderp_detail_cash_advance
                          where
                              voucher_no in %s""" % (payment_nos))
            diffSet = payment_nos
            if cr.rowcount>0:
                result = []
                for pn in cr.fetchall():
                    result.append(str(pn[0]))
                diffSet = set(voucherno_list).difference(set(result))

            if diffSet:
                raise osv.except_osv("KDVN Error","Please check Voucher Number, not available in ERP System !\n%s" % list(diffSet))

        return super(kderp_batch_update_advance_and_cash, self).load( cr, uid, fields, data, context)
kderp_batch_update_advance_and_cash()

class kderp_import_advance_and_cash_line(osv.osv):
    _name = "kderp.import.advance.and.cash.line"
    _description = "KDERP Import Advance And Cash Line"

    _columns={
              'paymentno':fields.char('Payment No.',size=32,required=True,select=True),
              'date_acc_recv_adv':fields.date('ReceivedRequestAdvance',),
              'date_acc_recv_cash':fields.date('ReceviceCashBookDate',),
              'payment_import_id':fields.many2one('kderp.batch.update.advance.and.cash','Payment Import',required=True),
              }
    _defaults = {

        }
kderp_import_advance_and_cash_line()