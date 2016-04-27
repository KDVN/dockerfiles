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
    'name':"KDERP Prepaid Purchase",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"Add new module Prepaid Purchase Module",
    'category':"KDERP Apps",
    'depends':['kderp_stock','kderp_purchase_extend','kderp_link'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'css': ['static/src/css/*.css'],
    'data':[
             "security/kderp_prepaid_purchase_security.xml",
             "security/ir.model.access.csv",
             "data/kderp_prepaid_purchase_code.xml",
             'wizard/allocate_to_job_view.xml',
             "views/kderp_prepaid_purchase_view.xml",
             'views/stock_view.xml',             
             "views/kderp_purchase_inherit_workflow.xml", # Move to kderp_stock
             "views/kderp_prepaid_purchase_line_detail_view.xml",
             "report/kderp_summary_cable_talking_from_stock_view.xml"
            ],
    'demo':[],
    'installable':True
}