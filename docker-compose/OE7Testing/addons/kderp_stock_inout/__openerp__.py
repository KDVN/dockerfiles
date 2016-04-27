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
    'name':"KDERP Stock IN/OUT/Move",
    'version':"7.0.0",
    'author':"KDERP IT-Dev. Team",
    'images' : ['images/kinden.png'],
    'summary':"Customize Stock Picking and Stock Move",
    'category':"KDERP Apps",
    'depends':['kderp_stock','kderp_purchase_extend'],
    'description': """
    - Customize Database structure and function
    - Customize Procedure
    - Customize Interface""",
    'data':[
            'security/kderp_stock_inout_security.xml',
            'security/ir.model.access.csv',
            'security/kderp_stock_inout_rule.xml',
            "views/kderp_stock_move_views.xml",
            "wizard/kderp_wizard_transfer_to.xml",
            'views/kderp_stock_picking_in_views.xml',
            # 'views/kderp_stock_picking_in_wopo_views.xml',
            'views/kderp_stock_picking_out_views.xml',
            'views/kderp_product_views.xml',
            'views/kderp_stock_picking_internal_views.xml',
            'views/kderp_stock_views.xml',
            'wizard/kderp_open_stock_products_views.xml',
            'views/kderp_purchase_view.xml',
            'views/kderp_stock_workflow.xml'
            ],
    'demo':[],
    'installable':True
}