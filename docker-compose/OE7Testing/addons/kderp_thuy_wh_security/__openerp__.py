{
    'name': "ThuyDemoSecurity",
    'version': '1.0',    
    'description': """
					Thuy Demo Security
					""",
    'depends': [
				'kderp_stock_expense', 
				'kderp_stock_inout', 
				'kderp_stock'],
    'data': [
				'security/kderp_thuy_wh_security.xml',
				'security/ir.model.access.csv',
				'views/kderp_thuy_wh_security_view.xml',
			],
    'demo': [],
}
