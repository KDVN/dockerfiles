##############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    'name' : 'Jasper Reports 7.0',
    'version' : '1.0',
    'author' : 'NaN·tic',
    'category' : 'Generic Modules/Jasper Reports',
    'description' : """
This module integrates Jasper Reports with OpenERP for version 7.0.
-------------------------------------------------------------------

Settings/Technical/Jasper Reports 7.0 (Jasper Reports for OpenERP version 7.0)

Modified original jasper_reports(OpenERP version 6.1) to work fine in OpenERP version7.0.

Credits to original Author.

Author: kankaungmalay(https://twitter.com/kankaungmalay)

    """,
    'website': 'http://www.nan-tic.com',
    'images' : [],
    'depends' : ["base",'web',"document_webdav"],
    'data': [
        'wizard/jasper_create_data_template.xml',
        'jasper_wizard.xml',
        'report_xml_view.xml',
        'security/ir.model.access.csv',
    ],
    'js': [
        
    ],
    'qweb' : [
        
    ],
    'css':[
        'static/src/css/jasper_internal.css',
    ],
    'demo': [
        
    ],
    'test': [
        
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
