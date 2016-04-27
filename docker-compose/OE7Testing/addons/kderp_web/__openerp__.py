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
    'name':"KDERP Web",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : [''],
    'summary':"Customize Web module",
    'category':"KDERP Apps",
    'depends':['base','web','share','base_import','document'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'css': ['static/src/css/*.css'],
    'js':['static/src/js/*.js'],
    'data':['res_users_view.xml'],
    'qweb':['static/src/xml/kderp_base.xml'],
    'demo':[],
    'installable':True
}