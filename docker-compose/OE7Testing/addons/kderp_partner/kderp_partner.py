from openerp.osv.orm import Model
from openerp.osv import fields
from openerp import osv

from openerp.tools.translate import _

import re

POSTAL_ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')
ADDRESS_FIELDS = POSTAL_ADDRESS_FIELDS + ('email', 'phone', 'fax', 'mobile', 'website', 'ref', 'lang', 'code')

class Bank(Model):
    _description='Bank'
    _name = 'res.bank'
    _inherit = 'res.bank'
    
    _columns={
              'short_name':fields.char('Short Name',size=8,help='Short Name using in Kinden Vietnam')
              }
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}        
        if name:
            ids = self.search(cr, uid, [('short_name', '=', name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('short_name', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('bic', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        if ids:
                return self.name_get(cr, uid, ids, context)
        return super(Bank,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
    
Bank()

class res_partner_bank(Model):
    _name='res.partner.bank'
    _inherit='res.partner.bank'
    
    def _prepare_name_get(self, cr, uid, bank_dicts, context=None):
        """ Format the name of a res.partner.bank.
            This function is designed to be inherited to add replacement fields.
            :param bank_dicts: a list of res.partner.bank dicts, as returned by the method read()
            :return: [(id, name), ...], as returned by the method name_get()
        """
        # prepare a mapping {code: format_layout} for all bank types
        bank_type_obj = self.pool.get('res.partner.bank.type')
        bank_types = bank_type_obj.browse(cr, uid, bank_type_obj.search(cr, uid, []), context=context)
        bank_code_format = dict((bt.code, bt.format_layout) for bt in bank_types)

        res = []
        for data in bank_dicts:
            name = data['acc_number']
            if data['state'] and bank_code_format.get(data['state']):
                try:
                    if not data.get('bank_name'):
                        data['bank_name'] = _('BANK')
                    name = bank_code_format[data['state']] % data
                except Exception:
                    raise osv.except_osv(_("Formating Error"), _("Invalid Bank Account Type Name format."))
            res.append((data.get('id', False), name))
        return res

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        bank_dicts = self.read(cr, uid, ids, context=context)
        return self._prepare_name_get(cr, uid, bank_dicts, context=context)
res_partner_bank()

class res_partner(Model):
    _name = 'res.partner'
    _description='Res Partner (Client, Owner and Supplier)'
    _inherit = 'res.partner'
    
    def address_get(self, cr, uid, ids, adr_pref=None, context=None):
        """ Find contacts/addresses of the right type(s) by doing a depth-first-search
        through descendants within company boundaries (stop at entities flagged ``is_company``)
        then continuing the search at the ancestors that are within the same company boundaries.
        Defaults to partners of type ``'default'`` when the exact type is not found, or to the
        provided partner itself if no type ``'default'`` is found either. """
        adr_pref = set(adr_pref or [])
        if 'default' not in adr_pref:
            adr_pref.add('default')
        result = {}
        visited = set()
        for partner in self.browse(cr, uid, ids, context=context):            
            current_partner = partner
            result['default']=partner.id
            for cp in partner.child_ids:
                if cp.type in adr_pref:
                    result[cp.type]=cp.id
        
        default = result.get('default', partner.id)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or default        
        return result
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
    
        if context.get('inactive', False):
            args += ['|',('active','=',True),('active','=',False)]
            
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            # search on the name of the contacts and of its company
            search_name = name
            if operator in ('ilike', 'like'):
                search_name = '%%%s%%' % name
            if operator in ('=ilike', '=like'):
                operator = operator[1:]
            
            ids = self.search(cr, uid, [('zip','=',search_name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('city',operator,search_name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name',operator,search_name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('trade_name', operator, search_name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('code',operator,search_name)] + args, limit=limit, context=context)
            
            if ids:                
                return self.name_get(cr, uid, ids, context)
        return super(res_partner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

    
    def _display_address(self, cr, uid, address, without_company=True, context=None):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''

        # get the information that will be injected into the display format
        # get the address format
        
        if not context:
            context={}
        if context.get('inline'):
            address_format = address.country_id and address.country_id.address_format or \
                  "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"

            args = {
                'state_code': address.state_id and address.state_id.code or '',
                'state_name': address.state_id and address.state_id.name or '',
                'country_code': address.country_id and address.country_id.code or '',
                'country_name': address.country_id and address.country_id.name or '',
                'company_name': address.parent_id and address.parent_id.name or '',
            }
                            
            address_field = ['title', 'street', 'street2', 'zip', 'city']
            for field in address_field :
                args[field] = getattr(address, field) or ''
            if without_company:
                args['company_name'] = ''
            elif address.parent_id:
                address_format = '%(company_name)s\n' + address_format
            if context.get('show_code',False):
                args['code']=address.parent_id.code if address.parent_id else address.code
                address_format="%(code)s - " + address_format
                
            return address_format % args
        else:
            address_format = address.country_id and address.country_id.address_format or \
                  "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        
            args = {
                'state_code': address.state_id and address.state_id.code or '',
                'state_name': address.state_id and address.state_id.name or '',
                'country_code': address.country_id and address.country_id.code or '',
                'country_name': address.country_id and address.country_id.name or '',
                'company_name': address.parent_id and address.parent_id.name or '',
            }
            address_field = ['title', 'street', 'street2', 'zip', 'city']
            for field in address_field :
                args[field] = getattr(address, field) or ''
            if without_company:
                args['company_name'] = ''
            elif address.parent_id:
                address_format = '%(company_name)s\n' + address_format
           
            return address_format % args
    
    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        
        sequence_no=0        
        for record in self.browse(cr, uid, ids, context=context):
            name = record.code + " - " + record.name if record.code else record.name 
            if record.parent_id:
                name =  ("%s - %s (%s)" % (record.parent_id.code, name, record.parent_id.name)) if record.parent_id.code else ("%s (%s)" % ( name, record.parent_id.name)) 
            if context.get('hide_name'):
                sequence_no+=1
                context['show_code']=True
                name = self._display_address(cr, uid, record, without_company=True, context=context)
                name = name.replace('\n\n','\n')
                name = name.replace('\n\n','\n')
                name = name.replace('\n',', ')
                name = name.replace(', ,',',')
                name = name.strip()
                if name[0]==',':
                    name = name[1:]
                if name[len(name)-1]==',':
                    name = name[:len(name)-2]
                name="%s. %s" % (sequence_no,name)
            elif context.get('show_address'):
                sequence_no+=1
                context['show_code']=True
                name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
                name = name.replace('\n\n','\n')
                name = name.replace('\n\n','\n')
                name="%s. %s" % (sequence_no,name)
            if context.get('show_email') and record.email:
                context['show_code']=True
                name = "%s <%s>" % (name, record.email)
            res.append((record.id, name))
        if len(res)==1 and sequence_no>0:
            key=res[0][0]
            res=dict(res)
            res[key]=res[key].replace('1. ','')
            res=[(key,res[key])]        
        return res
    
    def _newcode_suggest(self,cr,uid,context={}):
        selection=[]
#New code HCM
        codetype=''
        if context.get('default_customer',False):
            codetype='Customer'
        elif context.get('default_supplier',False):
            codetype='Supplier'
        cr.execute("Select prefix,newcode || ' - ' || name from vwnewcode_partner where name ilike '%%%s%%' order by newcode asc" % codetype)
        for newcode,desc in cr.fetchall():            
            selection.append((newcode,desc))
        return selection
    
    def _get_supplier(self, cr, uid, context=None):
        if not context:
            context = {}
        if 'default_parent_id' in context:
            return False
        return context.get('search_default_supplier',False)
        
    def _get_customer(self, cr, uid, context=None):
        if not context:
            context = {}
        if 'default_parent_id' in context:
            return False
        return context.get('search_default_customer',False)

    def _default_code(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('default_parent_id',False):
            cr.execute("""Select 
                            'A' || lpad((max(substring(substring(coalesce(rpc.code,'A00-' || rpp.code) from 1 for 3) from 2 for 2)::int)+1)::text,2,'0') || '-' || rpp.code
                        from 
                            res_partner rpp
                        left join
                            res_partner rpc on rpp.id = rpc.parent_id  and  rpc.code ilike 'A__-' || rpp.code
                        group by
                            rpp.id""")
            res = cr.fetchone()
            if res:
                return res[0]
        return False
       
    _columns={
              'trade_name':fields.char('Trade Name',size=25, select=True),
              
              'type': fields.selection( [('default','Default'),('location','Location'),('invoice','Invoice'), ('delivery','Delivery'), ('contact','Contact'), ('other','Other') ],'Address Type'),
              
              'child_ids': fields.one2many('res.partner', 'parent_id', 'Address'),
              'name': fields.char('Name', size=256, required=True, select=True,translate=True),
              
              'street': fields.char('Street', size=128,translate=True),
              'street2': fields.char('Street2', size=128,translate=True),
              'zip': fields.char('Zip', change_default=True, size=24,translate=True),
              'city': fields.char('City', size=128),
              
              'vat_code': fields.char('V.A.T.', size=32),
              'code': fields.char('Code', size=16, select=True),
              'newcode_suggest':fields.selection(_newcode_suggest,'New Code',size=16,store=False),
              'is_company': fields.boolean('Is a Company', help="Check if the contact is a company, otherwise it is a person"),
              }
    _defaults={
               'is_company':lambda self, cr, uid, ctx={}: False if 'default_parent_id' in ctx else True,
               'name':lambda self, cr, uid, ctx={}: 'N/A' if 'default_parent_id' in ctx else '',
               'code':_default_code,
               'customer':_get_customer,
               'supplier':_get_supplier
               }
    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The Code of the Partner must be unique !')]

    
    def write(self, cr, uid, ids, vals, context=None):
        # Update parent and siblings or children records
        if isinstance(ids, (int, long)):
            ids = [ids]
        if vals.get('is_company')==False:
            vals.update({'child_ids' : [(5,)]})
        for partner in self.browse(cr, uid, ids, context=context):
            update_ids = []
            if partner.is_company:
                domain_children = [('parent_id', '=', partner.id), ('use_parent_address', '=', True)]
                update_ids = self.search(cr, uid, domain_children, context=context)
            elif partner.parent_id:
                 if vals.get('use_parent_address')==True:
                     domain_siblings = [('parent_id', '=', partner.parent_id.id), ('use_parent_address', '=', True)]
                     update_ids = [partner.parent_id.id] + self.search(cr, uid, domain_siblings, context=context)
                 if 'use_parent_address' not in vals and  partner.use_parent_address:
                    domain_siblings = [('parent_id', '=', partner.parent_id.id), ('use_parent_address', '=', True)]
                    update_ids = [partner.parent_id.id] + self.search(cr, uid, domain_siblings, context=context)
            self.update_address(cr, uid, update_ids, vals, context)
        return super(res_partner,self).write(cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context={}
        if vals.get('parent_id',False):
            vals['supplier']=False
            vals['customer']=False
            
        # Update parent and siblings records
        if vals.get('parent_id') and vals.get('use_parent_address'):
            domain_siblings = [('parent_id', '=', vals['parent_id']), ('use_parent_address', '=', True)]
            update_ids = [vals['parent_id']] + self.search(cr, uid, domain_siblings, context=context)
            
            self.update_address(cr, uid, update_ids, vals, context)
        return super(res_partner,self).create(cr, uid, vals, context=context)

    def update_address(self, cr, uid, ids, vals, context=None):
        addr_vals = dict((key, vals[key]) for key in POSTAL_ADDRESS_FIELDS if vals.get(key))
        if addr_vals:
            return super(res_partner, self).write(cr, uid, ids, addr_vals, context)
    
    def onchange_suggest_code(self, cr, uid, ids,new_code,context={}):
        val = {}
        if new_code:
            prefix=new_code
            cr.execute("""Select newcode from vwnewcode_partner where prefix='%s'""" %prefix)
            val={'value':{'code':cr.fetchone()[0],'newcode_suggest':False},
                 'type': 'ir.actions.client',
                 'tag': 'reload'}
        return val
    
    def init(self,cr):
        cr.execute("""CREATE OR REPLACE VIEW vwnewcode_partner AS 
                            ((SELECT vwnewcode.prefix::text || btrim(to_char(max("substring"(vwnewcode.code::text, length(vwnewcode.prefix::text) + 1, length(vwnewcode.suffix::text))::integer) + 1, vwnewcode.suffix::text)) AS newcode, vwnewcode.name,prefix
                                               FROM ( SELECT isq.name, 
                                                            CASE
                                                                WHEN cnewcode.code IS NULL THEN (isq.prefix::text || isq.suffix::text)::character varying
                                                                ELSE cnewcode.code
                                                            END AS code, isq.prefix, isq.suffix
                                                       FROM ir_sequence isq
                                                  LEFT JOIN ( SELECT res_partner.code AS code
                                                               FROM res_partner
                                                              WHERE length(res_partner.code::text) in (( SELECT length(isq.prefix::text || isq.suffix::text) AS length
                                                                       FROM ir_sequence isq
                                                                      WHERE isq.code::text = 'kderp_supplier_code'::text AND isq.active
                                                                     ))) cnewcode ON cnewcode.code::text ~~ (isq.prefix::text || lpad(''::text, length(isq.suffix::text), '_'::text))
                                                 WHERE isq.code::text = 'kderp_supplier_code'::text AND isq.active) vwnewcode
                                              GROUP BY vwnewcode.prefix, vwnewcode.name, vwnewcode.suffix
                                    UNION 
                                             SELECT vwnewcode.prefix::text || btrim(to_char(max("substring"(vwnewcode.code::text, length(vwnewcode.prefix::text) + 1, length(vwnewcode.suffix::text))::integer) + 1, vwnewcode.suffix::text)) AS newcode, vwnewcode.name,prefix
                                               FROM ( SELECT isq.name, 
                                                            CASE
                                                                WHEN cnewcode.code IS NULL THEN (isq.prefix::text || isq.suffix::text)::character varying
                                                                ELSE cnewcode.code
                                                            END AS code, isq.prefix, isq.suffix
                                                       FROM ir_sequence isq
                                                  LEFT JOIN ( SELECT res_partner.code AS code
                                                               FROM res_partner
                                                              WHERE "substring"(res_partner.code::text, 1, 2) <> 'C9'::text AND "substring"(res_partner.code::text, 1, 3) <> 'CS9'::text AND length(res_partner.code::text) in (( SELECT length(isq.prefix::text || isq.suffix::text) AS length
                                                                       FROM ir_sequence isq
                                                                      WHERE isq.code::text = 'kderp_customer_code'::text AND isq.active
                                                                     ))) cnewcode ON cnewcode.code::text ~~ (isq.prefix::text || lpad(''::text, length(isq.suffix::text), '_'::text))
                                                 WHERE prefix!='C9' and isq.code::text = 'kderp_customer_code'::text AND isq.active) vwnewcode
                                              GROUP BY vwnewcode.prefix, vwnewcode.name, vwnewcode.suffix)
                            UNION 
                                     SELECT vwnewcode.prefix::text || btrim(to_char(max("substring"(vwnewcode.code::text, length(vwnewcode.prefix::text) + 1, length(vwnewcode.suffix::text))::integer) + 1, vwnewcode.suffix::text)) AS newcode, vwnewcode.name,prefix
                                       FROM ( SELECT isq.name, 
                                                    CASE
                                                        WHEN cnewcode.code IS NULL THEN (isq.prefix::text || isq.suffix::text)::character varying
                                                        ELSE cnewcode.code
                                                    END AS code, isq.prefix, isq.suffix
                                               FROM ir_sequence isq
                                          LEFT JOIN ( SELECT res_partner.code AS code
                                                       FROM res_partner
                                                      WHERE "substring"(res_partner.code::text, 1, 2) = 'C9'::text and length(res_partner.code::text) = (( SELECT length(isq.prefix::text || isq.suffix::text) AS length
                                                               FROM ir_sequence isq
                                                              WHERE isq.code::text = 'kderp_customer_code'::text AND isq.active
                                                             LIMIT 1))) cnewcode ON cnewcode.code::text ~~ (isq.prefix::text || lpad(''::text, length(isq.suffix::text), '_'::text))
                                         WHERE prefix='C9' and isq.code::text = 'kderp_customer_code'::text AND isq.active) vwnewcode
                                      GROUP BY vwnewcode.prefix, vwnewcode.name, vwnewcode.suffix)
                    UNION 
                             SELECT isq.prefix::text || btrim(to_char(max("substring"(rp.code::text, length(isq.prefix::text) + 1, length(rp.code::text) - length(isq.prefix::text))::integer) + 1, isq.suffix::text)) AS newcode, isq.name,prefix
                               FROM res_partner rp
                          LEFT JOIN ir_sequence isq ON "substring"(rp.code::text, 1, length(isq.prefix::text)) = isq.prefix::text
                         WHERE isq.active = true AND isq.code::text = 'kderp_supplier_code_han'::text
                         GROUP BY isq.prefix, isq.suffix, isq.name""")
res_partner()