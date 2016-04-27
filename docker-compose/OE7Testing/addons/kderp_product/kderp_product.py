from openerp.osv.orm import Model
from openerp.osv import fields

import re

class product_product(Model):
    _inherit='product.product'
    _name='product.product'
    _columns={
              'default_code' : fields.char('Code', size=16, select=True,required=True),
              'budget_id':fields.many2one('account.budget.post','Budget',help='Link to budget',ondelete="restrict"),
              'brand_ids':fields.one2many('kderp.product.brandname','product_id','Brands')
              }
    _sql_constraints=[('kderp_product_code','unique(default_code)','Code for Product must be unique !')]
        
    def name_get(self, cr, user, ids, context=None,from_obj=''):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []
        
        def _name_get(d):
            name = d.get('name','')
            code = d.get('default_code',False)
            if not from_obj:
                return (d['id'], code if code else name)
            elif from_obj=='pol':
                return (d['id'], name)
            if code:
                name = '[%s] %s' % (code,name)
            if d.get('variants'):
                name = name + ' - %s' % (d['variants'],)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.name,
                              'default_code': s.product_code or product.default_code,
                              'variants': product.variants
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.name,
                          'default_code': product.default_code,
                          'variants': product.variants
                          }
                result.append(_name_get(mydict))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('default_code',operator,name)]+ args, limit=limit, context=context)
            if not ids:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = set()
                ids.update(self.search(cr, user, args + [('default_code',operator,name)], limit=limit, context=context))
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    ids.update(self.search(cr, user, args + [('name',operator,name)], limit=(limit and (limit-len(ids)) or False) , context=context))
                ids = list(ids)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result    
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}
        if context and context.get('search_default_categ_id', False):
            args.append((('categ_id', 'child_of', context['search_default_categ_id'])))
        if 'job_id' in context:
            job_id = context.get('job_id',0)
            product_ids = []
            if not job_id:
                job_id=0
            cr.execute("""select 
                            pp.id
                        from 
                            product_product pp
                        left join
                            kderp_budget_data kbd on pp.budget_id = kbd.budget_id
                        where account_analytic_id=%s""" % job_id)
            
            for pr_id in cr.fetchall():
                product_ids.append(pr_id)
            args.append((('id', 'in', product_ids)))
        return super(product_product, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=False)

product_product()

class kderp_brand_name(Model):
    _name = 'kderp.brand.name'
    _description = 'KDERP Brand name'
    
    def search(self, cr, user, args, offset=0, limit=None, order=None,  context=None, count=False):
        if context:
            if 'pr_id' in context.keys():
                cr.execute("select \
                                brandname_id\
                            from \
                                kderp_product_brandname pp\
                            where\
                                product_id=%d" % context['pr_id'])
                res = cr.fetchall()
                res1=[]
                for tmp in res:
                    res1.append(tmp[0])
                var_filter=res1
                if res1:
                    args.append(('id','in',var_filter))
            #raise osv.except_osv(_('Invalid action !'),_('Cannot delete Request(s) which are in (%s) State1!' %args))
           # args.append
        return super(kderp_brand_name,self).search(cr, user, args, offset, limit, order,context, count)
    
    _columns={
              'code':fields.char('Code',size=10,required=True,select=1),
              'name':fields.char('Name',size=50,required=True,select=1),
              'product_ids':fields.one2many('kderp.product.brandname','brandname_id','Products')
             }
    _sql_constraints = [('code_unique_brandname', 'unique (name)', 'KDVN Error: Brand name must be unique !')] 
kderp_brand_name()

class kderp_product_brandname(Model):
    _name = 'kderp.product.brandname'
    _description = 'KDERP Product and Brand name'
    
    _order='default_brand desc'
    _columns={
              'brandname_id':fields.many2one('kderp.brand.name','Brand Name',required=True),
              'product_id':fields.many2one('product.product','Product'),
              'default_brand':fields.boolean('Default')
             }
    _sql_constraints = [('code_unique_brand_name', 'unique (partner_id)', 'KDVN Error: Brand name must be unique !')] 
    
    def create(self,cr, uid, vals, context=None):
        new_id = False
        new_id=Model.create(self,cr, uid, vals, context)
        if vals['default_brand'] and vals['product_id'] and new_id:
            cr.execute('Update kderp_brand_name set \
                                default_brand=False\
                            where product_id=%s and id<>%s' % (vals['product_id'],new_id))
        return new_id
    
    def write(self, cr, uid, ids, vals, context=None):
        Model.write(self, cr, uid, ids,vals,context=context)
        if vals['default_brand']:
            cr.execute('Update kderp_brand_name set \
                                default_brand=False\
                            where product_id=(Select product_id from kderp_brand_name where id=%s) and id<>%s' % (ids[0],ids[0]))
        return True
kderp_product_brandname()