from osv import osv, fields

# from pentaho_reports.core import Report 
# 
# class Report(Report):
#     def setup_report(self):
#         raise osv.except_osv("E","E")
        
class report_xml(osv.osv):
    _name = "ir.actions.report.xml"
    _inherit = "ir.actions.report.xml"

    _columns = {
                'convert_to_wizard':fields.boolean('Convert to Wizard'),
                'linked_action_window_id':fields.many2one("ir.actions.act_window","Linked Action"),
                'jasper_output': fields.selection([('html','HTML'),('csv','CSV'),('xls','XLS'),('rtf','RTF'),('odt','ODT'),('ods','ODS'),('txt','Text'),('pdf','PDF'),('docx','Microsoft Office Word (docx)'),('xlsx','Microsoft Office Word (xlsx)')], 'Jasper Output'),
                }
    _defaults = {
                 'convert_to_wizard':lambda *a: False,
                 'linked_action_window_id':lambda *a: False
                 }
    
    def update_print_action(self, cr, uid, id, context=None, delete=False):
        if id:
            for report_xml_obj in self.pool.get('ir.actions.report.xml').browse(cr, uid, id, context):
                values_obj=self.pool.get('ir.values')
                #raise osv.except_osv("E",report_xml_obj.linked_action_window_id.id)
                
                if report_xml_obj.convert_to_wizard and not delete:
                   if not report_xml_obj.linked_action_window_id:
                        view_ids=self.pool.get('ir.ui.view').search(cr, uid, [('model', '=', 'ir.actions.report.promptwizard'),('type','=','form')], context=context)
                
                        action_vals = {'name': report_xml_obj.name,
                                       'res_model': 'ir.actions.report.promptwizard',
                                       'type' : 'ir.actions.act_window',
                                       'view_type': 'form',
                                       'view_mode': 'tree,form',
                                       'view_id' : view_ids and view_ids[0] or 0,
                                       'context' : "{'service_name' : '%s'}" % report_xml_obj.report_name,
                                       'target' : 'new',
                                       }
                        action_id = self.pool.get('ir.actions.act_window').create(cr, uid, action_vals, context=context)
                       
                        value_data = {
                                    "name": report_xml_obj.name,
                                    "model": report_xml_obj.model,
                                    "key": "action",
                                    "object": True,
                                    "key2": "client_print_multi",
                                    "value": "ir.actions.act_window,%s" % action_id
                                    }
                        values_obj.create(cr, uid, value_data, context=context)
                        self.write(cr, uid, id, {'linked_action_window_id':action_id})
                        
                        values_ids = values_obj.search(cr, uid, [("value", "=", "ir.actions.report.xml,%s" % report_xml_obj.id)])
                        if values_ids:
                            values_obj.unlink(cr, uid, values_ids, context=context)
                   else:
                        re = values_obj.search(cr,uid, [("value", "=", "ir.actions.act_window,%s" % report_xml_obj.linked_action_window_id.id)])
                        if not re:
                            value_data = {
                                        "name": report_xml_obj.name,
                                        "model": report_xml_obj.model,
                                        "key": "action",
                                        "object": True,
                                        "key2": "client_print_multi",
                                        "value": "ir.actions.act_window,%s" % report_xml_obj.linked_action_window_id.id
                                        }
                            new_val_id = values_obj.create(cr, uid, value_data, context=context)
                            
                        values_ids = values_obj.search(cr, uid, [("value", "=", "ir.actions.report.xml,%s" % report_xml_obj.id)])
                        if values_ids:
                            values_obj.unlink(cr, uid, values_ids, context=context)
                            
                elif not report_xml_obj.convert_to_wizard or delete:
                    action_id = self.pool.get('ir.actions.act_window').unlink(cr, uid, report_xml_obj.linked_action_window_id.id, context=context)
                    
                    values_ids = values_obj.search(cr, uid, [("value", "=", "ir.actions.act_window,%s" % report_xml_obj.id)])
                    if values_ids:
                        values_obj.unlink(cr, uid, values_ids, context=context)
                    if not report_xml_obj.linked_menu_id:
                        values_ids = values_obj.search(cr, uid, [("value", "=", "ir.actions.report.xml,%s" % report_xml_obj.id)])
                        if not values_ids:
                            value_data = {
                                            "name": report_xml_obj.name,
                                            "model": report_xml_obj.model,
                                            "key": "action",
                                            "object": True,
                                            "key2": "client_print_multi",
                                            "value": "ir.actions.report.xml,%s" % report_xml_obj.id
                                            }
                            new_val_id = values_obj.create(cr, uid, value_data, context=context)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        res = self.update_print_action(cr, uid, ids,context,True)
        return super(report_xml, self).unlink(cr, uid, ids, context=context)
           
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default = default.copy()
        default.update({'created_menu_id' : 0,'convert_to_wizard':False,'linked_action_window_id':False})
        return super(report_xml, self).copy(cr, uid, id, default, context=context)

report_xml()