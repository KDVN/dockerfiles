import time
from datetime import datetime
from openerp.osv.orm import Model
from openerp.osv import fields, osv

import openerp.addons.decimal_precision as dp
import re

class kderp_asset_location(Model):
    _name='kderp.asset.location'
    _description="Physical Asset Location"
    _columns={
              'name':fields.char('Location',size=128,required=True)
              }
kderp_asset_location()

class kderp_job(Model):
    _name='kderp.job'
    
    _description='Job for Asset'
    _columns={
              'code':fields.char('Job Code',size=32),
              'name':fields.char('Job Name',size=128),
              }
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}

        if name:
            job_ids = self.search(cr, uid, [('code', '=', name)] + args, limit=limit, context=context)
            if not job_ids:
                job_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not job_ids:
                name = name.strip()
                job_ids = self.search(cr, uid,  [('name', 'ilike', name)] + args, limit=limit, context=context)
        else:
            job_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, job_ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        if type(ids).__name__!='list':
            ids=[ids]
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id,"%s - %s" %(elmt.code,elmt.name)))
        return res
    
    def update_job(self, cr, uid, ids, cron_mode=True, context=None):
#                             (Select id,code,name from "U_CodeJob" where code not in (Select code from account_analytic_account)
#                         Union
        cr.execute("""Insert into 
                        kderp_job (code,name)
                    Select 
                        trim(upper(code)),name
                    from account_analytic_account aaa
                    where trim(upper(code)) not in (Select trim(upper(coalesce(code,''))) from kderp_job)""")
        cr.execute("""Update kderp_job kj set name=aaa.NAME from account_analytic_account aaa where trim(upper(kj.code))=trim(upper(aaa.code))""")
        return True
#     
#     def init(self,cr):
#         cr.execute("""Insert into 
#                         kderp_job (id,code,name)
#                     Select 
#                         id,code,name          
#                     from          
#                     (Select id,code,name from "U_CodeJob" where code not in (Select code from account_analytic_account)
#                         Union
#                     Select id,code,name  from account_analytic_account where code not in (Select code from "U_CodeJob")) vwjob
#                     where id not in (Select id from kderp_job)""")
kderp_job()

class kderp_type_of_asset(Model):
    _name='kderp.type.of.asset'
    _description='KDERP Type Of Asset (Fixed Asset or Tool)'
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}
        
        if context.get('search_fixed_asset'):
            toa_ids= self.search(cr, uid, [('typeofasset_id', operator, name)] + args, limit=limit, context=context)                    
        elif name:
            toa_ids = self.search(cr, uid, [('name', '=', name)] + args, limit=limit, context=context)
            if not toa_ids:
                toa_ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
            if not toa_ids:
                name = name.strip()
                toa_ids = self.search(cr, uid,  [('description', 'ilike', name)] + args, limit=limit, context=context)
#             if isinstance(a,(float,int)) and not toa_ids and name!='FA':
#                 toa_ids = self.search(cr, uid,  [('name', '!=', 'FA'),('from_value','=',eval(name))] + args, limit=limit, context=context)
        else:
            toa_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, toa_ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        if type(ids).__name__!='list':
            ids=[ids]
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        list_name={'FA':'Fixed Asset','EQ':'Tools & Equipment','FM':'For Management'}
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id,"%s:%s->%s" %(list_name[elmt.name],"{:,}".format(elmt.from_value).strip(),"{:,}".format(elmt.to_value).strip())))
            
        return res
    
    _columns={
              'name':fields.selection([('FA','Fixed Asset'),('EQ','Tools & Equipment'),('FM','For Management')],'Type of Asset',required=True),
              'description':fields.char('Description',size=128),
              'from_value':fields.float('From Value',required=True),
              'to_value':fields.float('To Value',required=True),
              }
kderp_type_of_asset()
    
class kderp_asset_code(Model):
    _name = 'kderp.asset.code'
    _description='KDERP Asset Code'
    _order = 'code asc,id'
    
    def _get_full_name(self, cr, uid, ids, name, args, context=None):
        res={}
        for id in ids:
            language=context.get('lang','')
            elmt = self.browse(cr, uid, id, context=context)
            r_name=elmt.name
            context['lang']='vi_VN'
            name_vi = self.browse(cr, uid, id, context=context).name
            if language:
                context['lang']=language
            else:
                context.pop('lang')
            if r_name!=name_vi:
                r_name='%s / %s' % (r_name,name_vi)
            res[id]=r_name
        return res
    
    _columns={
              'code':fields.char('Code',size=4,required=True),
              'name':fields.char('Description',size=128,required=True,translate=True),
              #'asset_code_accounting_id':fields.many2one('kderp.asset.code.accounting','Accounting Code'),
              'child_ids':fields.one2many('kderp.asset.code','parent_id','Sub Code'),
              'parent_id':fields.many2one('kderp.asset.code','Parent Code'),
              'full_name':fields.function(_get_full_name,type='char',size=64,method=True,
                                          store={'kderp.asset.code':(lambda self, cr, uid, ids, c={}: ids, ['code','name'], 10)}
                                          )
              }
    _sql_constraints = [('asset_code_unique',"unique(code)","KDERP Error: The Asset Code must be unique !")]
    _constraints = [
        (osv.osv._check_recursion, 'Error ! You can not create recursive Asset Code.', ['parent_id'])
    ]
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}
        
        if name:
            asscode_ids = self.search(cr, uid, [('code', '=', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('name', '=', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            asscode_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, asscode_ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        dict_type={'1':'Tangible','2':'Intangible','3':'Others'}
        
        if type(ids).__name__!='list':
            ids=[ids]
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            language=context.get('lang','')
            elmt = self.browse(cr, uid, id, context=context)
            r_name=elmt.name
            context['lang']='vi_VN'
            name_vi = self.browse(cr, uid, id, context=context).name
            if language:
                context['lang']=language
            else:
                context.pop('lang')
            if r_name!=name_vi:
                r_name='%s - %s / %s' % (elmt.code, r_name, name_vi)
            else:
                r_name='%s - %s' % (elmt.code,elmt.name)
            res.append((id,"%s" %(r_name)))
        return res
    
kderp_asset_code()

class kderp_asset_code_accounting(Model):
    _name = 'kderp.asset.code.accounting'
    _description='KDERP Asset Code Accounting'

    _columns={
              'type':fields.selection([('1','Tangible'),('2','Intangible'),('3','Others')],'Type',required=True,
                                      help="""Tangible:Assets that have a physical form (items such as machinery, buildings and land, and current assets, such as inventory). 
                                              Intangible: An Asset that is not physical in nature (items such as software, patents, trademarks, copyrights, business methodologies))"""),
              'code':fields.char('Code',size=2,required=True),
              'name':fields.char('Description',size=128,required=True),
              'typeofasset_id':fields.many2one('kderp.type.of.asset','Type of Asset',required=True)              
              }
    _sql_constraints = [('asset_code_acc_type_unique',"unique(code,type)","KDERP Error: The Asset Code and type must be unique !")]
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}
            
        if context.get('search_fixed_asset'):
            asscode_ids = self.search(cr, uid, [('typeofasset_id', operator, name)] + args, limit=limit, context=context)
        elif name:
            asscode_ids = self.search(cr, uid, [('type', '=', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not asscode_ids:
                name = name.strip()
                asscode_ids = self.search(cr, uid,  [('name', 'ilike', name)] + args, limit=limit, context=context)
        else:
            asscode_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, asscode_ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        dict_type={'1':'Tangible','2':'Intangible','3':'Others'}
        
        if type(ids).__name__!='list':
            ids=[ids]
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id,"%s-%s: %s" %(dict_type[elmt.type],elmt.code,elmt.name)))
        return res
    
kderp_asset_code_accounting()

class kderp_asset_management(Model):
    _name = 'kderp.asset.management'
    _description='KDERP Asset Management'
    #SYSTEM METHOD
    
    _order='dateofpurchase desc,code desc'
    
    #Inherit Default ORM
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        asset_obj=self.browse(cr, uid, id)
        default.update({
           'code':self.get_new_code(cr, uid, False, asset_obj.type_asset_acc_id.id, asset_obj.asset_code_id.id, asset_obj.code, asset_obj.price, asset_obj.dateofinvoice)['value']['code']
        })
        res=super(kderp_asset_management, self).copy(cr, uid, id, default, context)
        self.pool.get('ir.rule').clear_cache(cr,uid)
        return res
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}

        if name:
            asscode_ids = self.search(cr, uid, [('code', '=', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('code', operator, name)] + args, limit=limit, context=context)
            if not asscode_ids:
                name = name.strip()
                asscode_ids = self.search(cr, uid, [('name', 'ilike', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                name = name.strip()
                asscode_ids = self.search(cr, uid, [('old_code', 'ilike', name)] + args, limit=limit, context=context)
        else:
            asscode_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, asscode_ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        res=[]
        if type(ids).__name__!='list':
            ids=[ids]
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id,"%s" %(elmt.code)))
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ots = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []

        for ot in ots:
            if ot['state'] not in ('draft', 'cancel'):
                raise osv.except_osv("KDERP Warning",'You cannot delete an Asset which is not processing.')
            else:
                unlink_ids.append(ot['id'])

        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    def get_new_code(self,cr, uid, ids, tangible, asset_code, code, price, date=time):
        if ids:
            return {}
        
        if not date:
            date=time
            
        if type(date).__name__=='str':
            date=datetime.strptime(date, '%Y-%m-%d')
        new_asset_code='H' if self.pool.get("res.users").browse(cr, uid, uid).location_user<>'hcm' else 'S'
        if not tangible:
            if ids:
                return {}
            return {'value':{'code':new_asset_code}}
        
        kaca=self.pool.get("kderp.asset.code.accounting").browse(cr, uid, tangible)
        new_asset_code = "%s%s%s" % (new_asset_code,kaca.typeofasset_id.name,kaca.type)
        
        r_warning=self.check_warning(cr, uid, ids,price, tangible)
        result={'value':{'code':new_asset_code}}
        result.update(r_warning)
        
        if not asset_code:
            if ids:
                return {}            
            return result
        
        kac=self.pool.get("kderp.asset.code").browse(cr, uid, asset_code)
        
        if kac.parent_id:
            kac_code=kac.parent_id.code
        else:
            kac_code=kac.code
            
        new_asset_code = "%s-%s-%s-" % (new_asset_code,kac_code.zfill(2),date.strftime('%y'))        
        cr.execute("""Select 
                        coalesce(max(substring(code from length('%s')+1 for 4)::int),0) as new_code
                    from 
                        kderp_asset_management where code ilike '%s' || '%%' and substring(code from length('%s')+1 for 4)~'^([0-9]+\.?[0-9]*|\.[0-9]+)$'""" % (new_asset_code,new_asset_code,new_asset_code))
        new_code=cr.fetchone()[0]
        new_code+=1
        new_asset_code="%s%s" % (new_asset_code,str(new_code).zfill(4))
        result={'value':{'code':new_asset_code}}
        result.update(r_warning)
        return result
        
    def check_warning(self,cr, uid, ids, price, tangible):
        r_warning={}
        if tangible and price:
            kaca=self.pool.get("kderp.asset.code.accounting").browse(cr, uid, tangible)
            from_value = kaca.typeofasset_id.from_value
            to_value = kaca.typeofasset_id.to_value            
            if (price<from_value) or (price>to_value and to_value>0):
                import locale
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                r_warning = {'warning':{'title':'KDERP Warning','message':'Please check input Price and Asset Type (%s==>%s)' % (locale.format('%.2f',from_value,True),locale.format('%.2f',to_value,True))}}
        return r_warning
    
    #onchange_typeofasset(type_asset_id,type_asset_acc_id,asset_code_id,code)
#     def onchange_asset_fixedtools(self, cr, uid, ids, tangible, asset_code, code,PODate=time): #Change fixed asset and tools
#         value={}
#         if not fixedtools:
#             dom={'type_asset_acc_id':[('id','!=',-1)]}
#         else:
#             type=False
#             typeofasset=self.pool.get('kderp.type.of.asset').browse(cr, uid, fixedtools).id
#             if typeofasset:
#                 new_dom=[('typeofasset_id','=',typeofasset)]
#                 if not tangible:                                         
#                     kaca_ids=self.pool.get('kderp.asset.code.accounting').search(cr, uid, new_dom)
#                     if len(kaca_ids)==1:
#                         value={'type_asset_acc_id':kaca_ids[0]}
#                 dom={'type_asset_acc_id':new_dom}
# 
#         if not code or not ids:
#             value.update(self.get_new_code(cr, uid, ids,tangible,typeofasset,asset_code, code, PODate))
#         return {'domain': dom,'value':value}
    
#     def onchange_asset_tangible(self, cr, uid, ids, tangible, asset_code, code):
#         #bk_typeofasset=fixedtools
#         value={}
#         if not tangible:
#             dom={'type_asset_id':[('id','!=',-1)]}
#         else:
#             typeofasset=self.pool.get('kderp.asset.code.accounting').browse(cr, uid, tangible).typeofasset_id
#             dom={'type_asset_id':[]}
#             if typeofasset:
#                 new_dom=[('id','=',typeofasset.id)]
#                 if not fixedtools:                                         
#                     ktos_ids=self.pool.get('kderp.type.of.asset').search(cr, uid, new_dom)
#                     if len(ktos_ids)==1:
#                         value={'type_asset_id':ktos_ids[0]}
#                 dom={'type_asset_id':new_dom}
#         if not code or not ids:
#             value.update(self.get_new_code(cr, uid, ids, tangible, bk_typeofasset, asset_code, code))                
#         return {'domain': dom,'value':value}
    
    def _get_current(self, cr, uid, ids, name, args, context=None):
        res={}
        kasm_ids=",".join(map(str,ids))
        cr.execute("""Select
                            kam.id,
                            user_id,
                            kamu.physical_location_id,
                            kamu.remarks,
                            kamu.job_id,
                            usedtime
                        from
                            kderp_asset_management kam
                        left join
                            kderp_asset_management_usage kamu on kam.id=asset_management_id and  (kam.id,usedtime) in (Select 
                                            asset_management_id,
                                            max(usedtime)
                                        from 
                                            kderp_asset_management_usage kamu
                                        where
                                            kamu.asset_management_id in (%s)
                                        group by
                                            asset_management_id)
                        where
                            kam.id in (%s)""" % (kasm_ids,kasm_ids))
        for k_id,u_id,pl_id,remark,job_id,dateofbeginning in cr.fetchall():
            res[k_id]={'current_user_id':u_id,
                       'physical_location_id':pl_id,
                       'current_remark':remark,
                       'current_job_id':job_id,
                       'dateofbeginning':dateofbeginning
                       }
        return res
    
    def _get_sub_assets(self, cr, uid, ids, name, args, context=None):
        res={}
        asset_ids=",".join(map(str,ids))
        cr.execute("""Select 
                        kam.id,
                        trim(array_to_string(array_agg(kam_sub.id::text),' '))::text
                    from
                        kderp_asset_management kam_sub
                    right join
                        kderp_asset_management kam on kam_sub.code ilike kam.code || '-%%'
                    where
                        kam.id in (%s)
                    Group by
                        kam.id""" % asset_ids)
        for id,list_asset_ids in cr.fetchall():
            if list_asset_ids:
                if list_asset_ids.isdigit():
                    list_asset_ids=[int(list_asset_ids)]
                else:
                    list_asset_ids=list(eval(list_asset_ids.strip().replace(' ',',').replace(' ','')))
            else:
                list_asset_ids=[]
            res[id]=list_asset_ids
        return res
    
    def _get_asset_from_asset_usage(self, cr, uid, ids, context=None):
        res=[]
        for kamu in self.pool.get('kderp.asset.management.usage').browse(cr,uid,ids):
            if kamu.asset_management_id:
                res.append(kamu.asset_management_id.id)
        return list(set(res))
    
    def _get_supplier(self, cr, uid, context={}):
        if not context:
            context = {}
        rp_id = context.get('partner_id', False)
        res = False
        if rp_id:
            rp_obj = self.pool.get('res.partner')
            res = rp_obj.browse(cr, uid, rp_id).name
        return res
   
    STATE_SELECTION=[('draft','Processing'),
                    ('inused', 'In Use'),
                    ('instock','In Stock'),
                    ('liquidated', 'Liquidated'),
                    ('outofdate', 'Out Of Date')]
    
    _columns={
              'code':fields.char('Code',size=32,required=True,readonly=True,states={'draft':[('readonly',False)]}),
              'refcode':fields.char('Ref. Code',size=32,readonly=True,states={'draft':[('readonly',False)]}),
              'old_code':fields.char('Old Code',size=32,readonly=True,states={'draft':[('readonly',False)]},help='Code from Access'),
              
              'asset_code_id':fields.many2one('kderp.asset.code','Asset Code',required=True,readonly=True,states={'draft':[('readonly',False)]}),
              #'type_asset_id':fields.many2one('kderp.type.of.asset','Fixed Asset/Tools',required=True,readonly=True,states={'draft':[('readonly',False)]}),
              'type_asset_acc_id':fields.many2one('kderp.asset.code.accounting','Asset Type',required=True,readonly=True,states={'draft':[('readonly',False)]}),
              
              'name':fields.text('Specification',readonly=True,states={'draft':[('readonly',False)]}),
              'supplier':fields.char('Supplier',size=128,readonly=True,states={'draft':[('readonly',False)]}),
              'dateofinvoice':fields.date('Invoice Date',readonly=True,states={'draft':[('readonly',False)]}),
              'dateofpurchase':fields.date('Purchase Date',readonly=True,states={'draft':[('readonly',False)]}),
              'dateofinput':fields.date('Input Date',readonly=True,states={'draft':[('readonly',False)]}),
              'dateofliquidated':fields.date('Liquidated Date',readonly=True,states={'inused':[('readonly',False)]}),
            
              'warranty_time':fields.integer('Warranty',readonly=True,states={'draft':[('readonly',False)]},help='Months warranty period'),
              
              'price':fields.float('Price',digits_compute=dp.get_precision('Amount'),readonly=True,states={'draft':[('readonly',False)]}),
              'quantity':fields.float('Quantity',digits_compute=dp.get_precision('Amount'),readonly=True,states={'draft':[('readonly',False)]}),
              'makername':fields.char("Maker Name",size=128,readonly=True,states={'draft':[('readonly',False)]}),
              'brandname':fields.char("Brand Name",size=128,readonly=True,states={'draft':[('readonly',False)]}),
              'usefullife':fields.integer('Useful life',readonly=True,states={'draft':[('readonly',False)]}),
              'state':fields.selection(STATE_SELECTION,'Status',readonly=True),
              'remarks':fields.text('Remarks'),
              
              'current_remark':fields.function(_get_current,method=True,type='char',size=256,string='Current Remark',multi='_get_current',
                                           store={
                                                  'kderp.asset.management.usage':(_get_asset_from_asset_usage,None,10),
                                                  'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['asset_usage_ids'], 10)
                                                  }),
              'current_user_id':fields.function(_get_current,method=True,type='many2one',relation='hr.employee',string='Current User',multi='_get_current',
                                           store={
                                                  'kderp.asset.management.usage':(_get_asset_from_asset_usage,None,10),
                                                  'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['asset_usage_ids'], 10)
                                                  }),
              'dateofbeginning':fields.function(_get_current,method=True,type='date',string='Date of beginning',multi='_get_current',
                                           store={
                                                  'kderp.asset.management.usage':(_get_asset_from_asset_usage,None,10),
                                                  'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['asset_usage_ids'], 10)
                                                  }),
              'current_job_id':fields.function(_get_current,method=True,type='many2one',relation='kderp.job',string='Current Job',multi='_get_current',
                                           store={
                                                  'kderp.asset.management.usage':(_get_asset_from_asset_usage,None,10),
                                                  'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['asset_usage_ids'], 10)
                                                  }),
              
              'physical_location_id':fields.function(_get_current,method=True,type='many2one',relation='kderp.asset.location',string='Current Physical Location',multi='_get_current',
                                           store={
                                                  'kderp.asset.management.usage':(_get_asset_from_asset_usage,None,10),
                                                  'kderp.asset.management':(lambda self, cr, uid, ids, c={}: ids, ['asset_usage_ids'], 10)
                                                  }),
              'parent_id':fields.many2one('kderp.asset.management','Related Asset', select=True, ondelete='restrict'),
              'related_asset_ids': fields.one2many('kderp.asset.management', 'parent_id', 'Related Asset'),
              'asset_usage_ids':fields.one2many('kderp.asset.management.usage','asset_management_id','Asset Usage',readonly=True,states={'inused':[('readonly',False)],'draft':[('readonly',False)]}),
              'sub_asset_ids':fields.function(_get_sub_assets,type='one2many',method=True,relation='kderp.asset.management', string='Sub Asset'),
              'active': fields.boolean('Active'),
              'asset_state':fields.selection([('usable','Usable'),('unstable','Unstable'),('broken','Broken')],'Asset State')              
              }
    
    _defaults={
               'active':True,
               'state':lambda *x:'draft',
               'dateofinput': lambda *a: time.strftime('%Y-%m-%d'),
               'asset_code_id':lambda *a:False,
               'quantity':lambda *a:1,
               'name':lambda self,cr, uid, context = {}: context.get('description',''),
               'supplier':_get_supplier,
               }
    
    _sql_constraints = [('asset_code_unique',"unique(code)","KDERP Error: The Asset Code must be unique !")]
     
    #Action Area
    def action_revised(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'draft'})

    def action_close(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'inused'})
    
    def action_submit(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'inused'})
    
    def action_liquidated(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'liquidated'})
    
    def action_outdated(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'outofdate'})
    def action_instock (self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,{'state':'instock'})
    
kderp_asset_management()

# class kderp_asset_management_related(Model):
#     _name="kderp.asset.management.related"
#     _description="KDERP Asset Management Related"
#     
#     _columns={
#               'asset_management_id':fields.many2one('kderp.asset.management','Asset'),
#               'state':fields.selection([('inused','In Used'),('moved','Moved'),('liquidated','liquidated')],'State'),
#               'remarks':fields.char('Remarks',size=128)
#               }    
# kderp_asset_management_related()

class kderp_asset_management_usage(Model):
    _name = 'kderp.asset.management.usage'
    _description='KDERP Asset Management Usage'
    _order='usedtime desc'
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if context is None:
            context={}

        if name:
            asscode_ids = self.search(cr, uid, [('user_id', '=', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('user_id', operator, name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('job_id', '=', name)] + args, limit=limit, context=context)
            if not asscode_ids:
                asscode_ids = self.search(cr, uid, [('job_id', operator, name)] + args, limit=limit, context=context)
        else:
            asscode_ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, asscode_ids, context=context)
    
    _columns={
              'asset_management_id':fields.many2one('kderp.asset.management','Asset',ondelete='restrict'),
              'job_id':fields.many2one('kderp.job','Job'),
              
              'user_id':fields.many2one('hr.employee','User',ondelete='restrict'),
              'manager_id':fields.many2one('hr.employee','Manager', ondelete='restrict'),
              'usedtime':fields.date('Used Date'),
              'endtime':fields.date('End Date'),
              'remarks':fields.char('Remarks',size=256),
              'physical_location_id':fields.many2one('kderp.asset.location','Physical Location', ondelete='restrict')
              }
    _defaults={
               'usedtime': lambda *a: time.strftime('%Y-%m-%d'),
               }
    #_sql_constraints = [('asset_code_unique',"unique(asset_management_id,user_id,usedtime)","KDERP Error: The Asset Code, Usera and Used Time must be unique !")]
kderp_asset_management_usage()