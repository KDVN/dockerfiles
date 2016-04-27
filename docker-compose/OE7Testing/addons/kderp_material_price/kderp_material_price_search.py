from osv import osv, fields
from osv.orm import intersect
from openerp import tools
import time

class material_price_wizard(osv.osv_memory):
    """
    Wizard dung de search du lieu material price
    """
    _name = 'material.price.wizard'
    _description = 'Material Price Search'
    
    def name_get(self, cr, uid, ids, context=None):
        if not context:
            context={}
        result=[]
        from time import strptime
        from datetime import datetime
        for e in self.browse(cr, uid, ids, context=context):
            from_date=datetime(*(strptime(e.period_start,("%Y-%m-%d"))[0:6])).strftime("%d-%b-%Y")
            to_date=datetime(*(strptime(e.period_end,("%Y-%m-%d"))[0:6])).strftime("%d-%b-%Y")
            result.append((e.id,"Material Price (%s ~ %s)" % (from_date,to_date)))
        return result
    
    def refresh(self, cr, uid, ids, context=None):
        return {
                'tag': 'reload',
                'type': 'ir.actions.act_window_close' 
                }
    
    def back(self, cr, uid, ids, context):
        """
        Quay tro lai view summary
        """
        self.write(cr, uid, context.get('material_price_wizard_id',False),{'material_price_unique_id':0})
        self.browse(cr, uid, context.get('material_price_wizard_id',False)).refresh()
        
        return {
                "type": "ir.actions.act_window",
                "name": "Search for Material Price",
                "res_model": "material.price.wizard",
                "res_id": context.get('material_price_wizard_id',False),
                "view_type": "form",
                "view_mode": "form",
                'target':'current',
                'nodestroy':True,
                'context':context,
                }
    def reset(self, cr, uid, ids, context):
        """
        Reset lai form - TODO
        """
        self._transient_vacuum(cr, uid, force=True)
        return True
#         return {
#                 "type": "ir.actions.client",
#                 "tag": "reload",
#                 }

    def _search_conditions(self, cr, uid, ids, name, args, context, name_str, spec_str):
        """
        Tra ve id_search, number_search, name_search1, name_search2, periods
        su dung de get_ids va get_pol_detail_ids
        """
        
        def _pos_neg_searchs(search_str="", opt_str=""):
            """
            Tra ve chuoi search positive va negative
            Phuc vu viec su dung % va ! cho search
            """
            if search_str:
                #Su dung regular express de tach dieu kien search
                #Neu phia cuoi chuoi co ! se dua them dieu kien search NOT vao
                import re
                #Tim dau ! o cuoi chuoi
                search_pattern = r'!'
                search_str = re.split(search_pattern, search_str)
                #Gan gia tri seach theo ILIKE
                positive_search = search_str[0].rstrip()
                if positive_search == "":
                    positive_search = "%%"
                if len(search_str) > 1:
                    negative_search = ""
                    for i in range(1,len(search_str)):
                        negative_search += opt_str %(search_str[i].rstrip())
                else:
                    negative_search = ""
            else:
                positive_search = "%%"
                negative_search = ""                
            return (positive_search, negative_search)
        
        #dieu kien search theo id, duoc tao boi ham hash (md5)
        if context.get('material_price_unique_id', False):
            id_search = "AND ABS(H_INT(LOWER(TRIM(pol.name)) || pol.product_id || product_uom || po.pricelist_id)) = %s" %(context.get('material_price_unique_id'))
        elif self.browse(cr, uid, ids[0], context).material_price_unique_id !=0:
            id_search = "AND ABS(H_INT(LOWER(TRIM(pol.name)) || pol.product_id || product_uom || po.pricelist_id)) = %s" %(self.browse(cr, uid, ids[0], context).material_price_unique_id)
        else:
            id_search = ""

        #dieu kien search theo period, number, name, spec
        for obj in self.browse(cr, uid, ids, context):
            period_start = obj.period_start
            period_end = obj.period_end
            if obj.number_search:
                number_search = obj.number_search
            else:
                number_search = "%%"

            name_search1 = _pos_neg_searchs(obj.name_search, name_str)[0]
            name_search2 = _pos_neg_searchs(obj.name_search, name_str)[1]
 
            spec_search1 = _pos_neg_searchs(obj.spec_search, spec_str)[0]
            spec_search2 = _pos_neg_searchs(obj.spec_search, spec_str)[1]
                
        res = {
               'id_search':id_search,
               'number_search': number_search,
               'name_search1': name_search1,
               'name_search2': name_search2,
               'spec_search1': spec_search1,
               'spec_search2': spec_search2,
               'period_start': period_start,
               'period_end': period_end
               }
        return res

    def _get_ids(self, cr, uid, ids, name, args, context={}):
        """
        Lay ids theo mot khoang thoi gian cua purchase_order_line
        Ghep product_id, uom va currency va name thanh mot id duy nhat
        Su dung hash
        """
        result={}

        name_str = " AND (pt.name !~* '%s') "
        spec_str = " AND (LOWER(TRIM(pol.name)) !~* '%s') "
        id_search = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['id_search']
        number_search = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['number_search']
        name_search1 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['name_search1']
        name_search2 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['name_search2']
        spec_search1 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['spec_search1']
        spec_search2 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['spec_search2']
        period_start = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['period_start']
        period_end = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['period_end']
        
        result[ids[0]]=[]
        if period_start and period_end:
            sql_string = """
                        SELECT ABS(H_INT(LOWER(TRIM(pol.name)) || pol.product_id || product_uom || po.pricelist_id)) as id,
                        --SELECT CAST(CAST(pol.product_id as TEXT)|| CAST(pol.product_uom AS TEXT) || CAST(po.pricelist_id AS TEXT) || CAST(ABS(H_INT(pol.name))AS TEXT) AS BIGINT) as id,
                        pp.default_code, pol.product_uom
                        FROM purchase_order_line pol
                        LEFT JOIN purchase_order po ON pol.order_id=po.id
                        LEFT JOIN product_product pp ON pol.product_id=pp.id
                            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id 
                        WHERE (pp.default_code !~* '^(4|5|6|7|8)') 
                            AND (po.date_order BETWEEN '%s' AND '%s') 
                            AND (pp.default_code ILIKE '%s')
                            AND (pt.name ILIKE '%s') 
                            %s
                            AND (LOWER(TRIM(pol.name)) ILIKE '%s')
                            %s
                            %s
                        GROUP BY pp.default_code, pol.product_id, pt.name, LOWER(TRIM(pol.name)), pol.product_uom, po.pricelist_id
                        ORDER BY pp.default_code, pol.product_uom 
                        """ % (period_start, period_end, number_search, name_search1, name_search2, spec_search1, spec_search2, id_search)
            cr.execute(sql_string)
            for uid in cr.fetchall():
                result[ids[0]].append(uid[0])
        return result
    
    def _get_pol_detail_ids(self, cr, uid, ids, name, args, context):
        result = {}
        
        name_str = " AND (pt.name !~* '%s') "
        spec_str = " AND (LOWER(TRIM(pol.name)) !~* '%s') "
        id_search = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['id_search']
        number_search = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['number_search']
        name_search1 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['name_search1']
        name_search2 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['name_search2']
        spec_search1 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['spec_search1']
        spec_search2 = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['spec_search2']
        period_start = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['period_start']
        period_end = self._search_conditions(cr, uid, ids, name, args, context, name_str, spec_str)['period_end']

        result[ids[0]]=[]

        if period_start and period_end:
            sql_string = """
                        SELECT pol.id as id
                        FROM purchase_order_line pol
                        LEFT JOIN purchase_order po ON pol.order_id = po.id
                        LEFT JOIN product_product pp ON pol.product_id=pp.id
                            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id 
                        WHERE (po.date_order BETWEEN '%s' AND '%s') 
                            AND (pp.default_code ILIKE '%s')
                            AND (pt.name ILIKE '%s') 
                            %s
                            AND (LOWER(TRIM(pol.name)) ILIKE '%s')
                            %s
                            %s
                        ORDER BY po.date_order DESC
                        """ % (period_start, period_end, number_search, name_search1, name_search2, spec_search1, spec_search2, id_search)
            #import pdb
            #pdb.trace_set()
            cr.execute(sql_string)
            for uid in cr.fetchall():
                result[ids[0]].append(uid[0])
        return result

    def _get_dates(self, cr, uid, context, period):
        """Tinh toan cac gia tri date ngam dinh"""
        from datetime import date
        if period == 'end':
            return time.strftime('%Y-%m-%d')
        elif period == 'start':
            return date(date.today().year, 1, 1).strftime('%Y-%m-%d')
        else:
            return False
#         return date(date.today().year, 1, 1).strftime('%Y-%m-%d')
        
    _columns = {
                'number_search': fields.char('By Number', size=30),
                'name_search': fields.char('By Name', size=30),
                'spec_search': fields.char('By Spec', size=30),
                'period_start': fields.date('Start Period',required=1),
                'period_end': fields.date('End Period',required=1),
                'material_price_unique_id': fields.integer('Unique ID'),
                'material_detail_ids': fields.function(_get_ids,obj='material.price', type="one2many", string="Detail", method=True),
                'pol_detail_ids': fields.function(_get_pol_detail_ids,obj='purchase.order.line', type="one2many", string="Purchase Line", method=True),
                }
    _defaults = {
                 'period_end':lambda self, cr, uid, context: self._get_dates(cr, uid, context, 'end'),
                 'period_start':lambda self, cr, uid, context: self._get_dates(cr, uid, context, 'start'),
                 }
material_price_wizard()

class material_price(osv.osv):
    _name = 'material.price'
    _description = 'Material Price'
    _auto = False
    #_inherit = 'purchase.order.line'

    def _get_values(self, cr, uid, ids, name, args, context={}):
        result = {}
        if not context:
            context={}

        for id in ids:
            result[id]={'min_price':1, 'max_price':3, 'avg_price':2}

        if ids:
            ids_str = ','.join(str(id) for id in ids) #I LOVE THIS ONE
            ids_str = "AND ABS(H_INT(LOWER(TRIM(pol.name)) || pol.product_id || product_uom || po.pricelist_id)) IN (%s)" %(ids_str)
        else:
            ids_str = ""

        period_start = context.get('period_start',False)
        period_end = context.get('period_end',False)
        
#         if not period_start or not period_end:
#             return result

        sql_string="""
               --SELECT CAST(CAST(pol.product_id as TEXT)|| CAST(pol.product_uom AS TEXT) || CAST(po.pricelist_id AS TEXT) || CAST(ABS(H_INT(pol.name))AS TEXT) AS BIGINT) as id,
               SELECT ABS(H_INT(LOWER(TRIM(pol.name)) || pol.product_id || product_uom || po.pricelist_id)) as id, 
               pol.product_id as product_id,
               min(pol.price_unit) as min_price,
               max(pol.price_unit) as max_price,
               avg(pol.price_unit) as avg_price
               FROM purchase_order_line pol
               LEFT JOIN purchase_order po on pol.order_id = po.id
               LEFT JOIN product_product pp on pol.product_id = pp.id
                   LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id 
               WHERE (pp.default_code !~* '^(4|5|6|7|8)')
               AND (po.date_order BETWEEN '%s' AND '%s') 
               %s 
               GROUP BY pp.default_code, pol.product_id, pt.name, LOWER(TRIM(pol.name)), pol.product_uom, po.pricelist_id
               ORDER BY pp.default_code, pol.product_uom 
               """ % (period_start, period_end, ids_str)
        
        cr.execute(sql_string)
        for obj in cr.dictfetchall():
            result[obj.pop('id')] = obj

        return result
   
    def _get_pol_ids(self, cr, uid, ids, name, args, context={}):
        
        result = {}
        result[ids[0]]=[]
        period_start = context.get('period_start',False)
        period_end = context.get('period_end',False)
        
        for obj in self.browse(cr, uid, ids, context):
            product_id = obj.product_id.id
            product_uom = obj.product_uom.id
            pricelist_id = obj.pricelist_id.id
            spec_dim = obj.spec_dim
        
        sql_string = """
                    SELECT pol.id as id
                    FROM purchase_order_line pol
                    LEFT JOIN purchase_order po ON pol.order_id = po.id
                    WHERE (po.date_order BETWEEN '%s' AND '%s') AND (CAST(pol.product_id AS TEXT) = '%s')
                    AND (LOWER(TRIM(pol.name)) = '%s')
                    AND (pol.product_uom ='%d') AND (po.pricelist_id = '%d')
                    ORDER BY po.date_order DESC
                    """ % (period_start, period_end, product_id, spec_dim, product_uom, pricelist_id)
        cr.execute(sql_string)
        for pol_id in cr.fetchall():
            result[ids[0]].append(pol_id[0])
        return result
    
    def pol_detail_show(self, cr, uid, ids, context):
        self.pool.get('material.price.wizard').write(cr, uid, context.get('material_price_wizard_id',False),{'material_price_unique_id':ids[0]})

        return {
                "type": "ir.actions.act_window",
                "name": "Material Price Wizard",
                "res_model": "material.price.wizard",
                "res_id": context.get('material_price_wizard_id',False),
                "view_type": "form",
                "view_mode": "form",
                'target':'current',
                'nodestroy':False,
                'context':context,
                }

    def pol_detail_back(self, cr, uid, ids, context):
        pass
    
    _columns = {
                'product_id': fields.many2one('product.product','Material'),
                'description': fields.text('Description'),
                'spec_dim': fields.text('Spec - DIM'),
                'product_uom': fields.many2one('product.uom','Unit'),
                'pricelist_id': fields.many2one ('product.pricelist','Currency'),
                'min_price': fields.function(_get_values, type='float', string = 'Min Price', method=True, multi='material_values'),
                'max_price': fields.function(_get_values, type='float', string = 'Max Price', method=True, multi='material_values'),
                'avg_price': fields.function(_get_values, type='float', string = 'Avg Price', method=True, multi='material_values'),
                'pol_ids': fields.function(_get_pol_ids, relation='purchase.order.line', type="one2many", string="Material Details", method=True),
                }
    
    def init(self,cr):
    ##Tao ham hash su dung de doi chuoi thanh integer
        cr.execute("""
                    create or replace function h_bigint(text) returns bigint as $$
                    select ('x'||substr(md5($1),1,16))::bit(64)::bigint;
                    $$ language sql;
                   """)
        cr.execute("""
                    create or replace function h_int(text) returns int as $$
                    select ('x'||substr(md5($1),1,8))::bit(32)::int;
                    $$ language sql;
                   """)
        
        tools.sql.drop_view_if_exists (cr, 'material_price')
        cr.execute("""
                CREATE OR REPLACE VIEW material_price AS (
                    --SELECT CAST(CAST(pol.product_id as TEXT)|| CAST(pol.product_uom AS TEXT) || CAST(po.pricelist_id AS TEXT) || CAST(ABS(H_INT(pol.name))AS TEXT) AS BIGINT) as id,
                    SELECT ABS(H_INT(LOWER(TRIM(pol.name)) || pol.product_id || product_uom || po.pricelist_id)) as id, 
                    pol.product_id, pt.name as description, LOWER(TRIM(pol.name)) as spec_dim, pol.product_uom, po.pricelist_id
                    FROM purchase_order_line pol
                    LEFT JOIN purchase_order po on pol.order_id = po.id
                    LEFT JOIN product_product pp on pol.product_id = pp.id
                        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    WHERE (pp.default_code !~* '^(4|5|6|7|8)')
                    --AND po.date_order BETWEEN DATE(CAST(EXTRACT(YEAR FROM NOW())-1 AS TEXT) || '-01-01') AND CURRENT_DATE
                    GROUP BY pp.default_code, pol.product_id, pt.name, LOWER(TRIM(pol.name)), pol.product_uom, po.pricelist_id
                    ORDER BY pp.default_code, pol.product_uom
                )
                   """)
material_price()

class purchase_order_line(osv.osv):
    """
    Ke thua purchase.order.line de show du lieu
    """
    _inherit = 'purchase.order.line'
    _name = 'purchase.order.line'

    def open_po(self, cr, uid, ids, context=None):
        if not context:
            context={}
 
        return {
            "type": "ir.actions.act_window",
            "name": "Purchase Order",
            "res_model": "purchase.order",
            "res_id":  self.browse(cr, uid, ids[0]).order_id.id,
            "view_type": "form",
            "view_mode": "form",
            'target':'current',
            'nodestroy':True,
            'context':context
        }
    _columns = {
              "date_order": fields.related('order_id','date_order',type='date',string='Date order'),
              "create_date": fields.date('Create date', readonly=True),
              }
    #_order = "create_date DESC"

purchase_order_line()