import time
from datetime import datetime
from openerp.osv.orm import Model
from openerp.osv import fields, osv

class kderp_asset_import(Model):
    _name = 'kderp.asset.import'
    _description='KDERP Asset Import'
    _order='name desc'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ots = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for ot in ots:
            if ot['state'] not in ('draft', 'cancel'):
                raise osv.except_osv("KDERP Warning",'You cannot delete imported data')
            else:
                unlink_ids.append(ot['id'])

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    def kderp_asset_submit(self, cr, uid, ids, context={}):
        for kai in self.browse(cr, uid, ids):
            done = True
            for kail in kai.detail_ids:
                if kai.import_type=='state':
                    if kail.state_asset and kail.state=='draft' and kail.asset_id.state <> 'liquidated':
                        if kail.state_asset =='liquidated':
                             write_data = {'state':kail.state_asset,
                                           'dateofliquidated':kail.date}
                        else:
                            write_data = {'state':kail.state_asset}
                        if kail.remarks:
                            old_remarks = kail.asset_id.remarks
                            new_remark = (old_remarks + '\n' + kail.remarks) if old_remarks else kail.remarks
                            write_data['remarks'] = new_remark
                        kail.asset_id.write(write_data)
                        kail.write({'state':'done'})
                    elif kail.state=='draft':
                        kail.write({'reason':'This asset already in Liquidation List'})
                        done = False
                elif kai.import_type=='spec':
                    write_data = {'name':kail.remarks}                    
                    kail.asset_id.write(write_data)
                    kail.write({'state':'done'})

                elif kai.import_type=='usage':                    
                        if not kail.user_id or not kail.date:
                            raise osv.except_osv("KDERP Warning","Pls. input user and used time")
                        try:
                            if kail.state=='draft':
                                create_data = {
                                               'user_id': kail.user_id.id,
                                               'manager_id': kail.manager_id.id if kail.manager_id else False,
                                               'job_id': kail.job_id.id if kail.job_id else False,
                                               'physical_location_id': kail.location_id.id if kail.location_id else False,
                                               'usedtime': kail.date,
                                               'remarks': kail.remarks
                                               }
                                kail.asset_id.write({'asset_usage_ids':[(0,0, create_data)]})
                                kail.write({'state':'done'})                            
                        except Exception, e:
                            kail.write({'reason':e})
                            done = False
            if done: 
                kai.write({'state':'done'})
        pass
        
    IMPORT_TYPE = (('state','State'),('usage','Usage'),('spec','Specification'))
    _columns={
              'name':fields.date("Import Date", 
                                    states={'done':[('readonly',True)]}, required=True),              
              'remarks':fields.char('Remarks',size=256, 
                                    states={'done':[('readonly',True)]}),                                                               
                
              'state':fields.selection((('draft','Draft'),('done','Completed')),'State',readonly=True),
              'detail_instock_ids':fields.one2many('kderp.import.asset.detail','import_id','Details',states={'done':[('readonly',True)]}),
              'detail_ids':fields.one2many('kderp.import.asset.detail','import_id','Details',states={'done':[('readonly',True)]}),
              'detail_spec_ids':fields.one2many('kderp.import.asset.detail','import_id','Details',states={'done':[('readonly',True)]}),
              'detail_usage_ids':fields.one2many('kderp.import.asset.detail','import_id','Details',states={'done':[('readonly',True)]}),
              'import_type':fields.selection(IMPORT_TYPE,'Import type',states={'done':[('readonly',True)]}),

              }
    _defaults={
               'name':lambda *a: time.strftime('%Y-%m-%d'),
               'state':lambda *a: 'draft'
               }    
    
kderp_asset_import()  

class kderp_import_asset_detail(Model):    
    _name = 'kderp.import.asset.detail'
    _rec_name = 'asset_id'

    def _get_state_asset(self, cr, uid, context=None):
        asset_state = self.pool.get('kderp.asset.management').fields_get(cr, uid, ['state'],{})
        tmp_selection = asset_state['state']['selection']
        return tuple(tmp_selection)

    _columns={
              'import_id':fields.many2one('kderp.asset.import','Import', required=True, states={'done':[('readonly',True)]}),
              'asset_id':fields.many2one('kderp.asset.management','Asset', required=True, states={'done':[('readonly',True)]}),
              'date':fields.date('Date', required=True, states={'done':[('readonly',True)]}),
              'user_id':fields.many2one('hr.employee','User', states={'done':[('readonly',True)]}),
              'state':fields.selection((('draft','Draft'),('done','Completed')),'State',readonly=True),
              'reason':fields.char("Reason", size=128, readonly = True),
              'manager_id':fields.many2one('hr.employee','Manager', states={'done':[('readonly',True)]}),
              'location_id':fields.many2one('kderp.asset.location','Location', states={'done':[('readonly',True)]}),
              'remarks':fields.char('Remark',size=256, states={'done':[('readonly',True)]}),
              'job_id':fields.many2one('kderp.job','Job', states={'done':[('readonly',True)]}),
              'state_asset':fields.selection(_get_state_asset, string='State Asset')
              }
    _defaults = {
                 'state':lambda *x: 'draft',
                 'state_asset':lambda *x: 'liquidated'
                 }
    _order = 'state desc'
    _sql_constraints = [('unique_asset_import','unique(import_id,asset_id)','KDERP Warning: Duplicated Asset, pls check')]