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
from openerp.tools.translate import _
from openerp import tools

class resource_resource(osv.osv):
    _name = "resource.resource"
    _inherit = "resource.resource"
    _description = "Resource Detail"
    _columns = {
        'name' : fields.char("Name", size=64, required=True,translate=True),
            }
resource_resource()

class hr_employee(osv.osv):
    _name = "hr.employee"
    _description = "KDERP Customize Employee"
    _inherit = "hr.employee"
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name','staffno'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['staffno']:
                name = "%s - %s" % (name,record['staffno'])
            res.append((record['id'], name))
        return res
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search(cr, user, [('staffno', '=ilike', name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)
    
    def _get_full_name(self, cr, uid, ids, name, args, context=None):
        res={}
        for khre in self.browse(cr, uid, ids, context):
            res[khre.id]="%s - %s" % (khre.staffno,khre.name)
        return res
    
    _columns = {
                'staffno':fields.char("Staff Number",size=8,required=True),
                'full_name':fields.function(_get_full_name,type='char',size=64,method=True,
                                            store={
                                                   'hr.employee': (lambda self, cr, uid, ids, c={}: ids, ['name','staffno'], 5),
                                                   })
                }
    _sql_constraints = [('kderp_unique_staff_no', 'unique(staffno)', 'KDERP Error: The number of staff must be unique!')]
    
    _order='staffno, name_related'
hr_employee()

class hr_department(osv.osv):
    _name = "hr.department"
    _inherit = "hr.department"
    
    _columns={
              'manager_2nd_id':fields.many2one('res.users','2nd Manager'),
              'code':fields.char('Code',size=8)
              }        
hr_department()

class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context):
            name = record.name
            if record.employee_id:                
                name = "%s - %s" % (record.employee_id.staffno,name)
            res.append((record['id'], name))
        return res
    
    def _get_employee(self, cr, uid, ids, name, args, context=None):
        res={}
        for ru in self.browse(cr, uid, ids, context):
            res[ru.id]=False
            for eple in ru.employee_ids:
                res[ru.id]=eple.id
        return res
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        if not context:
            context={}
        ids = []
        staffNumber=''
        
        if name:
            ids = self.search(cr, user, [('login','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
            if not ids and name.find('-')>0:
                ids = self.search(cr, user, [('name',operator,name.split('-')[1].strip())]+ args, limit=limit, context=context)
                staffNumber=name.split('-')[0].strip().upper()
            if not staffNumber and not ids:
                name=name.upper()
                try:
                    if int(name)>=0 and int(name)<=9999:
                        staffNumber='S' + name.zfill(4)
                except:
                    if name[:1]=='S':
                        staffNumber=name
            if not ids and staffNumber:
                cr.execute("Select id from hr_employee where staffno ilike '%s%%'" % staffNumber)
                hr_ids=[]
                ids=[]
                for hr_id in cr.fetchall():
                    hr_ids.append(hr_id[0])
                for hr in self.pool.get('hr.employee').browse(cr, user, hr_ids):
                    if hr.user_id:
                        ids.append(hr.user_id.id)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)

    _columns = {
        'employee_ids': fields.one2many('hr.employee', 'user_id', 'Related employees'),
        'employee_id': fields.function(_get_employee,type='many2one',method=True,relation='hr.employee', string='Related Employee'),
        }

res_users()
