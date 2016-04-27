from jasper_reports import *

def __init__(self, report, model, pool, cr, uid, ids, context):
        if not context:
            context = {}
        context['jasper_report_special'] = True        
        self.report = report
        self.model = model
        self.pool = pool
        self.cr = cr
        self.uid = uid
        self.ids = ids
        self.context = context
        self._languages = []
        self.imageFiles = {}
        self.temporaryFiles = []
        self.logger = logging.getLogger(__name__)        
        
JasperReports.BrowseDataGenerator.__init__ =  __init__

class ir_rule(osv.osv):
    _name = 'ir.rule'
    _inherit = 'ir.rule'
    
    def domain_get(self, cr, uid, model_name, mode='read', context=None):        
        if not context:
            context = {}
        if context.get('jasper_report_special', False):
            return [], [],  ['"'+self.pool.get(model_name)._table+'"']
        else:
            return super(ir_rule, self).domain_get(cr, uid, model_name, mode, context)