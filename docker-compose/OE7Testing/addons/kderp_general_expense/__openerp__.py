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
    'name':"KDERP General Expense",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"New Module add General Expense, extend from Job and Other Expense",
    'category':"KDERP Apps",
    'depends':['kderp_job_summary'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""", 
    'data':[
            "security/kderp_general_expense_group.xml",
            "security/ir.model.access.csv",
            "wizard/kderp_allocation_sheet_wizard_view.xml",
            "data/kderp_general_exepense_code_sequence.xml",            
            "views/kderp_general_expense_menu.xml",
            "views/kderp_budget_view.xml",
            "views/kderp_general_expense_yearly_view.xml",
            "views/kderp_general_expense_view.xml",
            "views/kderp_supplier_payment_general_expense_view.xml",
            "views/kderp_other_expense_view.xml",
            "views/kderp_departments_view.xml",
            "views/kderp_general_expense_tel_fee_view.xml",
            "views/kderp_general_expense_accounting_import_view.xml",
            "data/kderp_check_update_exp.xml",
            #"views/kderp_batch_update_view.xml",
            "security/kderp_general_expense_rule.xml",
            'wizard/update_monthly_expense_view.xml',
            'views/kderp_job_menu_view.xml',
            'views/kderp_job_view.xml',
            'wizard/kderp_ge_wizard_form_report_view.xml',
            ],
    'demo':[],
    'installable':True
} 
