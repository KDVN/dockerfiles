{
    'name':'GDT Companies',
    'version':'7.0.0',
    'author':"KDERP IT-Dev. Team",
    'summary':"Module for Getting companies data from GDT",
    'category':"KDERP Apps",
    'depends':['base','kderp_base'],
    'description': """
    - Enter VAT code can show relevant info from GDT database
    - Easy to find for a list (from excel file)
    - Must Install Depends easy_install -U beautifulsoup4 and apt-get install python-http-parser
    """,
    'data':[                      
            "security/kderp_gdt_companies_security.xml",           
            "security/ir.model.access.csv",
            "kderp_gdt_companies.xml",
            "kderp_update_view.xml"
            ],
    'demo':[],
    'css': ['static/src/css/*.css'],
    'js':['static/src/js/*.js'],
    'installable':True,
    
}