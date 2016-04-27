# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.osv.osv import object_proxy
import openerp.pooler as pooler
from openerp.tools.translate import _

class kderp_search(object_proxy):
    
    def _check_number(self,value):
        try:
            return float(value)
        except:
            return False
        
    def _check_date(self,value):
        #import time
        from time import *
        date = value
        try:
            if len(date)==10:
                valid_date = strptime(date, '%d/%m/%Y')
            else:
                valid_date = strptime(date, '%d/%m/%y')
        except:
            try:
                if len(date)==10:
                    valid_date = strptime(date, '%Y/%m/%d')
                else:
                    valid_date = strptime(date, '%y/%m/%d')
            except:
                return False
        
        return strftime('%Y/%m/%d',valid_date)
          
    def execute_cr(self, cr, uid, model, method, *args, **kw):
        fct_src = super(kderp_search, self).execute_cr
        if method=='search':
            fo=open("/home/dnt/a.txt",'a')
            fo.write(str(args))
            fo.write("\n")
            fo.close()
            for dom in args[0]:
            	if isinstance(dom,list):
                    if isinstance(dom[2],str):
                        if dom[2].find('@')>=0 and dom[2].find('~')>=1:
                            mf=pooler.get_pool(cr.dbname).get('ir.model.fields')
                           
                            value_search=dom[2].strip()
                            field_name=dom[0]
                            pos=value_search.find("~")
                            f_ids = mf.search(cr, uid, [('model','=', model), ('name','=',field_name)], context={})
                            if f_ids:
                                ttype=mf.read(cr, uid, f_ids[0],['ttype'])['ttype']
                                if ttype in ('text','char','date','datetime','float','integer','many2one'):
                                    pos_dom=args[0].index(dom)
                                    original_condition=args[0].pop(pos_dom)
                                    
                                    from_value=value_search[1:pos]
                                    to_value=value_search[pos+1:]
    
                                    if ttype=='date':
                                        from_value=from_value.replace(' ','').replace("-","/").strip()
                                        to_value=to_value.replace(' ','').replace("-","/").strip()
                                        
                                        from_value=self._check_date(from_value)
                                        to_value=self._check_date(to_value)
                                        
                                        if not from_value or not to_value:
    										raise osv.except_osv(
                                                                _('KDERP Warning'),
                                                                _('Input Invalid Date Format, please check %s') % value_search)
                                    elif ttype in ('float','integer'):
                                        from_value=from_value.replace(' ','').replace(",","")
                                        to_value=to_value.replace(' ','').replace(",","")
                                        
                                        from_value=self._check_number(from_value)
                                        to_value=self._check_number(to_value)
                                        #raise osv.except_osv("E","%s--%s" % (from_value,to_value))
                                        if isinstance(from_value,bool) or isinstance(from_value,bool):
    										raise osv.except_osv(
                                                                _('KDERP Warning'),
                                                                _('Input Invalid Number Format, please check %s') % value_search)
                                            
                                    from_args=['%s' % field_name,'>=',from_value]
                                    to_args=['%s' % field_name,'<=',to_value]
                                    args[0].insert(pos_dom,to_args)
                                    args[0].insert(pos_dom,from_args)
                                    args[0].insert(pos_dom,'&')
                                	
        return fct_src(cr, uid, model, method, *args, **kw)
    
    
kderp_search()