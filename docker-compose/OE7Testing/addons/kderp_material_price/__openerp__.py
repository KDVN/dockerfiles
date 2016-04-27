{
    'name':'Material Price',
    'version':'7.0.0',
    'author':"KDERP IT-Dev. Team",
    'summary':"Module for Material Unit Price for Estimation Dept.",
    'category':"KDERP Apps",
    'depends':['kderp_historical'],
    'description': """
    - Can lookup for any material price
    - Up to date value
    - Easy to find
    """,
    'data':['security/kderp_material_price.xml',
            'security/ir.model.access.csv',
            'kderp_material_price_search.xml',
            "res_config_view.xml",
            'kderp_material_price.xml',
            "wizard/kderp_update_price_wizard_view.xml",
            "wizard/kderp_update_latest_price_data_view.xml",
            "data/kderp_get_price_data.xml"
            ],
    'demo':[],
    'css': ['static/src/css/*.css'],
    'js':['static/src/js/*.js'],
    'installable':True,
    
}