{
    'name':'Get Information From Web',
    'version':'7.0.0',
    'author':"KDERP IT-Dev. Team",
    'summary':"Module for Getting companies data from GDT",
    'category':"KDERP Apps",
    'depends':['kderp_gdt_companies'],
    'description': """
    - Enter VAT code can show relevant info from GDT database
    - Easy to find for a list (from excel file)
    - Must Install Depends easy_install -U beautifulsoup4 and apt-get install python-http-parser
    """,
    'data':[           
            "get_data_fromweb_wizard.xml"
            ],
    'demo':[],
    'css': ['static/src/css/*.css'],
    'js':['static/src/js/*.js'],
    'installable':True,
    
}