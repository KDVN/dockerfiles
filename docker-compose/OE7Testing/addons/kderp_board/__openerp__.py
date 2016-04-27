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
    'name':"KDERP Board",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"Customize Base module",
    'category':"KDERP Apps",
    'depends':['base','kderp_job_summary'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':["security/kderp_dashboard_group_sercurity.xml",
            "action/kderp_action_job.xml",
            "action/kderp_action_quotation.xml",
            "action/kderp_action_contract.xml",
            "action/kderp_action_client_payment.xml",
            "action/kderp_action_other_expense.xml",
            "action/kderp_action_purchase.xml",
            "security/kderp_dashboard_group_rule_for_purchase.xml",
            "security/kderp_dashboard_group_rule_for_quotation.xml",
            'security/kderp_dashboard_group_rule_client_payment.xml',
            "security/kderp_dashboard_group_rule_contract_client.xml",
            "security/kderp_dashboard_group_rule_project.xml",
            "security/kderp_dashboard_group_rule_supplier_payment.xml",
            'security/ir.model.access.csv',
            "security/kderp_dashboard_group_rule_other_expense.xml",
            "security/kderp_dashboad_payment_group_rule.xml",
            "kderp_board_view.xml",
            "data/kderp_board_data.xml"
            ],
    'demo':[],
    'installable':True
}