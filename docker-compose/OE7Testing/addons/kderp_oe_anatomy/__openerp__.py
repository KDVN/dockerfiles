# __openerp__.py
{
    'name': "Web Example",
    'description': "Basic example of a (future) web module",
    'category': 'Hidden',
    'depends': ['web'],
    'data':['kderp_oe_anatomy.xml'],
    'js':['static/src/js/first_module.js'],
    'css':['static/src/css/kderp_oe_anatomy.css'],
    'qweb':['static/src/xml/kderp_oe_anatomy.xml'],
    'test':['static/src/tests/timer.js'],
}