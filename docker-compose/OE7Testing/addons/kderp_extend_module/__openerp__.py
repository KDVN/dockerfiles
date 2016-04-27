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
    'name':"KDERP Extend Module",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"Add new module Extend Module for Suiteable Kinden Procedure",
    'category':"KDERP Apps",
    'depends':['kderp_payment','kderp_job_summary','kderp_project_location',],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':[
             "security/kderp_extend_security.xml",
             "security/ir.model.access.csv",
             "kderp_supplier_payment_menu.xml",
             #"kderp_extend_project_view.xml",
             "kderp_payment_view.xml",
             "kderp_extend_payment_only_attached_view.xml",
             "kderp_extend_project_location_view.xml",
             "kderp_other_expense_view.xml",
             'wizard/update_contract_status_view.xml',
             "kderp_extend_contract_only_attached_view.xml",
             'data/kderp_extend_module_data.xml',
             "kderp_extend_quotation_view.xml",
             "kderp_extend_job_only_attached_view.xml",
             "kderp_extend_attachment_view.xml",
             'kderp_extend_purchase_view.xml',
             'kderp_extend_contract_view.xml',
             'kderp_invoice_view.xml',
             'kderp_extend_employee_view.xml' ,
             'kderp_extend_client_payment_view.xml',
             'kderp_extend_supplier_payment_view.xml',
             'kderp_extend_base_view.xml',             
             "security/kderp_extend_kderp_supplier_payment_security.xml",
             "security/kderp_extend_kderp_supplier_payment_expense_security.xml",
             'wizard/create_contract_from_quotation_view.xml',
             'kderp_budget_view.xml',
             'wizard/kderp_job_wizard_form_report_view.xml',
             'wizard/update_quotation_completion_date_view.xml',
             #'wizard/kderp_ge_wizard_form_report_view.xml',
             'kderp_city_view.xml'
            ],
    'demo':[],
    'installable':True
}