# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
import time

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.osv import fields, osv, expression
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.misc import unquote as unquote

class ir_rule(osv.osv):
    _name = 'ir.rule'
    _inherit = 'ir.rule'
        
    def clear_cache_cron(self, cr, uid, ids, cron_mode=True, context=None):
        self._compute_domain.clear_cache(self)
        return True
    
    def _domain_force_get(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        eval_context = self._eval_context(cr, uid)
        for rule in self.browse(cr, uid, ids, context):
            tmp_domain=str(rule.domain_force)            
            if tmp_domain.find("%s")>0:                         
                tmp_domain=eval(rule.domain_force)
                for dom in filter(lambda x: x[2].find("%s")>0,tmp_domain):                    
                    tdom = list(dom)
                    str_query=str(tdom[2])
                    cr.execute(str_query % uid)
                    tmp_ids=cr.fetchall()
                    list_ids=[]
                    for i in tmp_ids:
                        list_ids.append(i[0])
                    tdom[2] = tuple(list_ids)
                    tdom = tuple(tdom)
                    tmp_domain[tmp_domain.index(dom)] = tdom
                res[rule.id] = expression.normalize_domain(eval(str(tmp_domain), eval_context))
                #res[rule.id] = eval(tmp_domain)
                    #res[rule.id] = eval("[('"+tmp_domain[0][0]+"','"+tmp_domain[0][1]+"',"+str(list_ids)+")]")
                
            elif tmp_domain.find('.sql.query')>0:
                tmp_domain=eval(rule.domain_force)
                for dom in filter(lambda x: x[2].find(".sql.query")>0,tmp_domain):
                    tdom = list(dom)
                    str_query=str(tdom[2])                    
                    str_query=str_query.replace('.sql.query','')
                    cr.execute(str_query)
                    tmp_ids=cr.fetchall()
                    list_ids = []
                    for i in tmp_ids:
                        list_ids.append(i[0])
                    tdom[2] = tuple(set(list_ids))
                    tdom = tuple(tdom)
                    tmp_domain[tmp_domain.index(dom)] = tdom
                res[rule.id] = expression.normalize_domain(eval(str(tmp_domain), eval_context))
            elif rule.domain_force:
                res[rule.id] = expression.normalize_domain(eval(rule.domain_force, eval_context))
            else:
                res[rule.id] = []
        return res

    _columns = {
        
        'domain': fields.function(_domain_force_get, string='Domain', type='text'),
    }

ir_rule()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: