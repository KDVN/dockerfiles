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

from osv import fields,osv
from osv.orm import except_orm
import tools

class kderp_project_location(osv.osv):
    _name = 'kderp.project.location'   
    _rec_name = 'address'
    _description = 'KDERP Project Location'
   
    _columns = {
#         'account_analytic_id':fields.many2one('account.analytic.account','Job',select=1,ondelete="restrict",
#                                                      required=True),  
        'address':fields.char('Address',size=128,required=True,translate =True),
        'notes':fields.char('Notes',size=128),
    }
    _sql_constraints=[('kderp_project_location','unique(address)','Address Location must be unique !')]
   
kderp_project_location()
