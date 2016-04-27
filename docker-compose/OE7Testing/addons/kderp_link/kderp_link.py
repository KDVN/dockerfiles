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

class kderp_link_server(osv.osv):
    _name = 'kderp.link.server'
    _description = 'KDERP Link Server'
    
    def check_server_connection(self, cr, uid, ids, context = {}):
        from kderp_base import kderp_base
        if not ids:
            ids = self.search(cr, uid, [('need_to_check','=',True)])
        for kls in self.browse(cr, uid, ids):
            if not kderp_base.check_connection(kls.server, kls.port):
                raise osv.except_osv("KDERP Warning","There is an error while connecting to remote server. Please contact KINDEN VIETNAM OpenERP Administrator. We are sorry for this inconvenience.")
        pass
    def _get_connection(self, cr, uid, ids, name, arg, context=None):
        if not context:
            context = {}
        res = {}
        for kls in self.browse(cr, uid, ids, context):
            res[kls.id] ="dbname=%s port=%s host=%s user=%s password=%s" % (kls.database, kls.port, kls.server, kls.user, kls.password) 
        return res
    
    _columns = {        
                'server':fields.char('Server', size=32, required = True),
                'port':fields.integer('Port', required = True),
                'user':fields.char('User name', size=16, required = True),
                'password':fields.char('Password', size=64, required = True),
                'database':fields.char('Database', size=32, required = True),
                'name':fields.char("Description", required = True),
                'need_to_check':fields.boolean('Check?'),
                'connection_string':fields.function(_get_connection, type='char', size=256, method = True,
                                                    store={'kderp.link.server': (lambda self, cr, uid, ids, c={}: ids, None, 20),
                                                           }),
                'link_server_line':fields.one2many('kderp.link.server.line','link_server_id','Detail'),
    }
    _defaults ={
                'port':5432,
                'need_to_check': True,
                }
    _sql_constraints =[("sql_unique_link_server_name",'unique(name)','KDERP Warning: Name for Server Link must unique'),
                       ("sql_unique_database_name",'unique(server, database, user)','KDERP Warning: Server and database must be unique'),
                       ]
    
    def init(self, cr):
        cr.execute("""select * from pg_extension where extname='dblink'""")
        if not cr.rowcount:
            cr.execute("""CREATE EXTENSION dblink;""")
kderp_link_server()

class kderp_link_server_line(osv.osv):
    _name = 'kderp.link.server.line'
    _description = 'KDERP Link Server Line'
    
    STATE_SELECTION = (('draft','Draft'),('done','Done'))    
        
    _columns = {        
                'table_link_name':fields.char('Table Link Name', size=32, required = True, readonly = True, states = {'draft':[('readonly',False)]}),
                'table_definition':fields.text('Table Definition', required = True, readonly = True, states = {'draft':[('readonly',False)]}),
                'remote_query':fields.text('Remote Query', required = True, readonly = True, states = {'draft':[('readonly',False)]}),
                'link_server_id':fields.many2one('kderp.link.server','Server', required = True, readonly = True, states = {'draft':[('readonly',False)]}),
                'state':fields.selection(STATE_SELECTION, 'State', readonly = True, required = True),
                'name':fields.char("Description", required = True)
    }
    _defaults ={
                'state':'draft'
                }
    _sql_constraints =[("sql_unique_line_name",'unique(name)','KDERP Warning: Name for Server Link Line must unique'),
                       ("sql_unique_line_table",'unique(table_link_name, link_server_id)','KDERP Warning: Name for Server Link Line table and server must unique'),
                       ]
    def unlink(self, cr, uid, ids, context=None):
        todo_ids = []
        for klsl in self.browse(cr, uid, ids, context):
            if klsl.state=='draft':
                todo_ids.append(klsl.id)
            else:
                raise osv.except_osv("KDERP Warning", "Can delete this record")
        return osv.osv.unlink(self, cr, uid, todo_ids, context=context)
    
    def action_open(self, cr, uid, ids, context):
        return self.write(cr, uid, ids, {'state':'draft'}, context)
    
    def action_create_table_link(self, cr, uid, ids, context):
        if not context:
            context = {}
        for klsl in self.browse(cr, uid, ids, context):
            #Create table remote
            tblOriginal = klsl.table_link_name
            tblName = klsl.table_link_name + "_remote"
            vwName = 'vw' + tblName 
            tblDefinition = klsl.table_definition
            connStr = klsl.link_server_id.connection_string
            remoteQuery = klsl.remote_query
            
            #SQLTable = 'CREATE TABLE IF NOT EXISTS %s (%s);' % (tblName, tblDefinition)
            
            SQLView = """CREATE VIEW %s AS Select *  from 
                                        dblink('%s', '%s') as 
                                        %s (%s)""" % (vwName, 
                                                      connStr, remoteQuery,
                                                      tblOriginal, tblDefinition)
            #Create remote table
            #cr.execute(SQLTable)
            #Create remote View
            tools.drop_view_if_exists(cr, vwName)
            cr.execute(SQLView)
            klsl.write({'state':'done'})
kderp_link_server_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: