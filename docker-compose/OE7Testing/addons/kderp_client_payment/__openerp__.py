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
    'name':"KDERP Client Payment",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : [''],
    'summary':"Inherit and customize Account (Invoice) module",
    'category':"KDERP Apps",
    'depends':['kderp_common','kderp_account','kderp_project','kderp_quotation'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':['security/kderp_client_payment_group_sercurity.xml',
            'security/ir.model.access.csv',
            'data/kderp_client_payment_code.xml',
            #'voucher_payment_receipt_view.xml',
            'kderp_client_payment_view.xml',
            "kderp_received_view.xml",
            'kderp_invoice_view.xml',
            'kderp_contract_view.xml',
            #"kderp_project_view.xml"
            ],
    'demo':[],
   # 'css': ['static/src/css/kderp_client_payment.css'],
    'installable':True
}