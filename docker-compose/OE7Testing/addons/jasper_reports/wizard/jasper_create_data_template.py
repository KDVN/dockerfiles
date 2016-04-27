#import wizard
import pooler
import base64
from osv import osv,fields
from tools.translate import _

class create_data_template(osv.osv_memory):
    _name = 'jasper.create.data.template'
    _description = 'Create data template'

    def action_create_xml(self, cr, uid, ids, context=None):
        for data in  self.read(cr, uid, ids, context=context):
            model = self.pool.get('ir.model').browse(cr, uid, data['model'][0], context=context)
            xml = self.pool.get('ir.actions.report.xml').create_xml(cr, uid, model.model, data['depth'], context)
            self.write(cr,uid,ids,{
                'data' : base64.encodestring( xml ), 
                'filename': 'template.xml'
            })
        #return True

        ###########################################################################
        # Added this code snippet intending Jasper report 
        # (openobject-jasper-report-6.1)
        # works fine in openERP v7
        ###########################################################################
        model_data_obj = self.pool.get('ir.model.data')
        view_rec = model_data_obj.get_object_reference(cr, uid, 'jasper_reports', 'view_pos_box_out') # get_object_reference(cr, uid, module, xml_id)
        view_id = view_rec and view_rec[1] or False

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id' : [view_id],
            'res_id': ids[0],
            'res_model': self._name,
            'target': 'new',
            # save original model in context, because selecting the list of available
            # templates requires a model in context
            #'context': {
            #    'default_model': model,
            #},
            'context': context,
        }
        ###########################################################################
        # End
        ###########################################################################

    _columns = {
        'model': fields.many2one('ir.model', 'Model', required=True),
        'depth': fields.integer("Depth", required=True),
        'filename': fields.char('File Name', size=32),
        'data': fields.binary('XML')
    }

    _defaults = {
        'depth': 1
    }    
create_data_template()