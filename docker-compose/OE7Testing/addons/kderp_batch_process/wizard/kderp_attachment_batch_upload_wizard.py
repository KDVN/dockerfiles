# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv

import netsvc
import pooler
import time

import sys,os
from tools import config
import pooler
import base64

def _update_attach_common(self, cr, uid, folder,model,code='name',dup=False,deletedup=False):
    root = config.get('auto_folder_upload',"/media/auto_attachment")
    root_path = os.path.join(root,folder)
    #Dau cach dau tien
    root_path_attached = os.path.join(root,folder,'Attached')
    Error_Path = os.path.join(root,folder,'Error')
    pool = pooler.get_pool(cr.dbname)
    attach_obj = pool.get(model)
    
    document_obj = pool.get('ir.attachment')
    import shutil
    # TODO dup for the future, Now allow Duplicate    
    #for path, subdirs, files in os.walk(root_path): #Include Subdir
    for name in os.listdir(root_path):
        #for name in files:
        if name.upper() not in ['ATTACHED','OLD','ATTACHED (OLD)','ERROR']:
            chk_roa = False
            chk_contract = False
            tmp_name=name.strip()
            pos=tmp_name.find(' ')
            if pos<0:
                pos = tmp_name.find('.')
            if pos<0:
                pos=len(tmp_name)
            find_code = tmp_name[:pos]
            res_id = attach_obj.search(cr,uid,[(code,'ilike',find_code)])
            attchable = False
            
            if res_id:
                res_id = res_id[0]
            else:
                res_id = False
            
            if res_id and not dup:
                att_find = document_obj.search(cr, uid, [('name','=',tmp_name),('res_id','=',res_id),('res_model','=',model)])
                if not att_find:
                    attchable=True                
            if res_id and not dup and deletedup:
                att_find = document_obj.search(cr, uid, [('name','=',tmp_name),('res_id','=',res_id),('res_model','=',model)])
                if att_find:
                    document_obj.unlink(cr, uid, att_find)
            if res_id:
                full_path = os.path.join(root_path,name)
                
                datas = base64.encodestring(file(full_path, 'rb').read())
                
                if model=='purchase.order':
                    find_roa = name.upper().find('ROA')
                    find_contract = name.upper().find('CONTRACT')
                    
                    if find_roa>=0:
                        chk_roa = True
                    if find_contract>=0:
                        chk_contract = True
                    chk_amount = attach_obj.search(cr,uid,[('id','=',res_id),('amount_total','>=',15000000)])
                    vals = {'res_id':res_id,'res_model':model,'datas_fname':tmp_name,'datas':datas,'name':tmp_name} #,'title':tmp_name
                    try:
                        if chk_amount:
                            vals = {'res_id':res_id,'res_model':model,
                                    'datas_fname':tmp_name,'datas':datas,'name':tmp_name,
                                    'roa_comaprison_attached':chk_roa,'contract_attached':chk_contract} #,'title':tmp_name,
                            new_id = document_obj.create(cr,uid,vals,{})
                        else:
                            vals = {'res_id':res_id,'res_model':model,
                                    'datas_fname':tmp_name,'datas':datas,'name':tmp_name,
                                    'roa_comaprison_attached':False,'contract_attached':True,'quotation_attached':False} #,'title':tmp_name,
                            new_id = document_obj.create(cr,uid,vals,{})
                            
                        dst_folder = os.path.join(root_path_attached,name)
                        
                        src_file = full_path
                                                
#                         if os.path.exists(dst_folder):
#                             os.remove(dst_folder)
                        shutil.move(src_file, dst_folder)
                        
                        #os.rename(src_file, dst_folder)
                        cr.commit()
                    except Exception as e:
                        cr.rollback()
                        #raise osv.except_osv("E","%s-%s-%s" % (e,src_file,dst_folder))
                        continue
                else:                        
                    try:
                        vals = {'res_id':res_id,'res_model':model,
                                        'datas_fname':tmp_name,'datas':datas,'name':tmp_name} #,'title':tmp_name,
                        new_id = document_obj.create(cr,uid,vals,{})
                                            
                        dst_folder = os.path.join(root_path_attached,name)
                        src_file = full_path                        
                        #os.rename(src_file, dst_folder)
                        shutil.move(src_file, dst_folder)
                        cr.commit()
                    except Exception as e:
#                          raise osv.except_osv("E","%s-%s-%s" % (e,src_file,dst_folder))
                         cr.rollback()
                         continue
                    
            #raise osv.except_osv("E",str(res_id) + find_code)
    return {}

class attachment_auto_upload(osv.osv):
    _name = 'attachment.auto.upload'
    _auto = False
    
    def update_attach_po(self, cr, uid, ids, context):
        #res_model = 'purchase.order'
        try:
            res = _update_attach_common(self,cr,uid,'PO','purchase.order')
            cr.commit()
        except:
            pass
        try:
            res = _update_attach_common(self,cr,uid,'PO','kderp.purchase.general.contract')
            cr.commit()
        except:
            pass
        try:
            res = _update_attach_common(self,cr,uid,'Asset/Asset','kderp.asset.management','code',False,True)
            cr.commit()
        except:
            pass
        return {}
    
attachment_auto_upload()
