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
    'name':"KDERP Job & Contract Extend Module",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"Add new module Job & Contract Module",
    'category':"KDERP Apps",
    'depends':['kderp_extend_module'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':[
            "security/kderp_extend_job_and_contract.xml",
            "security/ir.model.access.csv",
            "views/kderp_control_area_view.xml",
            "views/kderp_extend_project_view.xml",
            "views/kderp_extend_contract_view.xml",
            "views/res_config_view.xml",

            "wizard/kderp_job_ongoing_list_wizard_form_report_view.xml"
            ],
    'demo':[],
    'installable':True
}