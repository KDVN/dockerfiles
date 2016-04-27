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
    'name':"KDERP Supplier Payment",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"Customize Invoice for Suiteable Kinden Procedure",
    'category':"KDERP Apps",
    'depends':['kderp_purchase','account','kderp_other_expense'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':[
            "security/kderp_supplier_payment_security.xml",
            "security/ir.model.access.csv",
            "data/kderp_supplier_payment_code.xml",
            "kderp_supplier_payment_view.xml",
            "kderp_supplier_vat_invoice_view.xml",
            "kderp_supplier_payment_workflow.xml",
            "kderp_purchase_view.xml",
            "kderp_supplier_payment_expense_workflow.xml",
            "kderp_supplier_payment_expense_view.xml",
            "kderp_expense_view.xml"
            ],
    'demo':[],
    'installable':True
}