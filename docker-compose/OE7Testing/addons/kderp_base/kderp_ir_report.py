from osv import osv, fields

class report_xml(osv.osv):
    _name = "ir.actions.report.xml"
    _inherit = "ir.actions.report.xml"

    _columns = {
               # 'convert_to_wizard':fields.boolean('Convert to Wizard'),
              #  'linked_action_window_id':fields.many2one("ir.actions.act_window","Linked Action")
                }
    _defaults = {
                # 'convert_to_wizard':lambda *a: False,
                # 'linked_action_window_id':lambda *a: False
                 }
    
    def _update_print_action(self, cr, uid, id, context=None, delete=False):
        if id:
            report_xml_obj = self.browse(cr, uid, id)
            values_obj=self.pool.get('ir.values')
            if report_xml_obj.convert_to_wizard and not delete:
                self.pool.get("ir.model").browse(cr, uid, vals["pentaho_report_model_id"], context=context).model
                
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
                            "name": report.name,
                            "model": report_xml_obj.model,
                            "key": "action",
                            "object": True,
                            "key2": "client_print_multi",
                            "value": "ir.actions.act_window,%s" % action_id
                            }
                values_obj.create(cr, uid, value_data, context=context)
                self.write(cr, uid, id, {'linked_action_window_id':action_id})
            elif report_xml_obj.convert_to_wizard and delete:
                values_ids = values_obj.search(cr, uid, [("value", "=", "ir.actions.report.xml,%s" % report.id)])
                if values_ids:
                    values_obj.unlink(cr, uid, values_ids, context=context)
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        res = self._update_print_action(cr, uid, ids[0],context,True)
        return super(report_xml, self).unlink(cr, uid, ids, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default = default.copy()
        default.update({'created_menu_id' : 0,'convert_to_wizard':False})
        return super(report_xml, self).copy(cr, uid, id, default, context=context)

report_xml()