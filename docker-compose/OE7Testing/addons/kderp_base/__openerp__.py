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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     d
#
##############################################################################
{
    'name':"KDERP Base",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : [''],
    'summary':"Customize Base module",
    'category':"KDERP Apps",
    'depends':['base','web'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':["data/kderp_base_data.xml",
            "security/kderp_base_security.xml",
            'kderp_base_view.xml',
            'kderp_users_view.xml',
            'ir_module_view.xml',
            'kderp_res_currency_view.xml',
            "kderp_config_view.xml"
            ],
    #'css': ['static/src/css/kderp_base.css'],
    #'js': ['static/src/js/*.js'],
    'demo':[],
    'installable':True
}