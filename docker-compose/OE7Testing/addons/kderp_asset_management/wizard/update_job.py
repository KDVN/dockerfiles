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

from lxml import etree

from openerp import tools
from openerp.tools.translate import _
from openerp.osv import fields, osv

class kderp_asset_update_job(osv.osv_memory):
    _name = 'kderp.asset.update.job'
    _description = 'Task Delegate'

    _columns = {
    }

    def update_job(self, cr, uid, ids, context=None):
        res=self.pool.get('kderp.job').update_job(cr, uid, ids)
        return True

kderp_asset_update_job()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
