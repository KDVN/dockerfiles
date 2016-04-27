from openerp.osv import fields, osv
    
class kderp_supplier_payment_expense(osv.osv):
    _name = 'kderp.supplier.payment.expense'
    _inherit = 'kderp.supplier.payment.expense'
    
    def _get_payment_from_ge(self, cr, uid, ids, context):
        if not context:
            context = {}
        res = {}
        for ge in self.pool.get('kderp.other.expense').browse(cr, uid, ids, context):
            for pge in ge.supplier_payment_expense_ids:
                res[pge.id] = True
        return res.keys()
    
    def onchange_date_ge(self, cr, uid, ids, date, oldno):
        cr.execute("Select location_user from res_users where id=%s" % uid)
        res = cr.fetchone()[0]
        chk_ignore =  False
        due_date = date
       
        if due_date and not chk_ignore:
            #due_date = self.pool.get('kdvn.common.function').check_date(date)
            due_date = self._onchange_due_date(cr,uid,ids,date)
        
        val={}
        
        if (not oldno and date) or (date and oldno and date[:4][2:]!=oldno[:4][2:]):
            cr.execute("""SELECT
                            wnewcode.pattern || 
                            btrim(to_char(max(substring(wnewcode.code::text, length(wnewcode.pattern) + 1,padding )::integer) + 1,lpad('0',padding,'0'))) AS newcode
                        from
                            (
                            SELECT 
                            isq.name,
                            isq.code as seq_code,
                            isq.prefix || to_char(DATE '%s', suffix || lpad('_',padding,'_')) AS to_char, 
                            CASE WHEN cnewcode.code IS NULL 
                            THEN isq.prefix::text || to_char(DATE '%s', suffix || lpad('0',padding,'0'))
                            ELSE cnewcode.code
                            END AS code, 
                            isq.prefix::text || to_char(DATE '%s', suffix) AS pattern,
                            padding,
                            prefix
                            FROM 
                                ir_sequence isq
                            LEFT JOIN 
                            (SELECT 
                                kderp_supplier_payment_expense.name AS code
                            FROM 
                                kderp_supplier_payment_expense
                            WHERE
                                length(kderp_supplier_payment_expense.name::text)=
                                ((SELECT 
                                length(prefix || suffix) + padding AS length
                                FROM 
                                ir_sequence
                                WHERE 
                                ir_sequence.code::text = 'kderp.supplier.payment.ge.code'::text LIMIT 1))
                            ) cnewcode ON cnewcode.code::text ~~ (isq.prefix || to_char(DATE '%s',  suffix || lpad('_',padding,'_')))
                            WHERE isq.code::text = 'kderp.supplier.payment.ge.code'::text AND isq.active) wnewcode
                        GROUP BY 
                            pattern, 
                            name,
                            seq_code,
                            prefix,
                            padding;""" %(date,date,date,date))
            res = cr.fetchone()
            if res:
                val={'name':res[0]}
        if due_date:
            val['due_date']=due_date
        return {'value':val}
    
    _columns={              
              #Relation Field
              'allocated_to': fields.related('expense_id', 'allocated_to', type='char', size=32, string='Allocated to', select = 1,
                                             store={
                                                    'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['expense_id'], 15),
                                                    'kderp.other.expense': (_get_payment_from_ge, ['allocated_to'], 15),
                                                    }),
              'section_incharge_id': fields.related('expense_id', 'section_incharge_id', type='many2one',relation='hr.department', size=32, string='Section Incharge', select = 1,
                                             store={
                                                    'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['expense_id'], 15),
                                                    'kderp.other.expense': (_get_payment_from_ge, ['section_incharge_id'], 15),
                                                    }),
              'supplier_id': fields.related('expense_id', 'partner_id', type='many2one',relation='res.partner', size=32, string='Supplier', select = 1,
                                             store={
                                                    'kderp.supplier.payment.expense': (lambda self, cr, uid, ids, c={}: ids, ['expense_id'], 15),
                                                    'kderp.other.expense': (_get_payment_from_ge, ['partner_id'], 15),
                                                    }),
              
              }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if not context:
            context = {}        
        if not view_id:            
            ge = False
            active_model = context['active_model'] if 'active_model' in context else False 
            if 'active_id' in context:
                active_id = context['active_id']
            elif 'active_ids' in context:
                active_id = context['active_ids'][0]
            else: 
                active_id = False
            if active_id and active_model:
                active_obj = self.pool.get(active_model)
                if active_model=='kderp.supplier.payment.expense':
                    ge = active_obj.browse(cr, uid, context['active_id']).expense_id.account_analytic_id.general_expense
                elif active_model=='kderp.other.expense':
                    ge = active_obj.browse(cr, uid, context['active_id']).account_analytic_id.general_expense
                elif active_model=='account.analytic.account':
                    ge = active_obj.browse(cr, uid, context['active_id']).general_expense                    
            if context.get('general_expense', False) or ge:
                views_ids = self.pool.get('ir.ui.view').search(cr, uid, [('name','=','kderp.supplier.payment.ge.%s' % view_type)])
                if views_ids:
                    view_id = views_ids[0]             
        return super(kderp_supplier_payment_expense, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)