from osv import osv, fields

class kderp_total_budget_cat(osv.osv):
    _name = 'kderp.total.budget.cat'
    _description = 'KDERP Total Budget Check Input'
    _auto = False
    
    _columns={
         "material":fields.float("Material"),
         "sub_contractor":fields.float('Sub-Contractor'),
         "site_expense":fields.float("Site-Expense"),
         "kinden_salary_admin_cost":fields.float("Salary, Admin. Cost"),
         "bussiness_profit":fields.float("Business Profit"),
         "total":fields.float("Total"),
         "id":fields.integer("ID")
        }

    def init(self, cr):
        cr.execute("""Create or replace view kderp_total_budget_cat as 
                        Select 
                            id,
                            sum(material) as material,
                            sum(sub_contractor) as sub_contractor,
                            sum(site_expense) as site_expense,
                            sum(kinden_salary_admin_cost) as kinden_salary_admin_cost,
                            sum(bussiness_profit) as bussiness_profit,
                            sum(material)+sum(site_expense)+sum(sub_contractor)+sum(kinden_salary_admin_cost)+sum(bussiness_profit) as total
                        from
                            (Select
                                account_analytic_id as id,
                                sum(coalesce(planned_amount,0)) as material,
                                0 as sub_contractor,
                                0 as site_expense,
                                0 as kinden_salary_admin_cost,
                                0 as bussiness_profit
                            from 
                                kderp_budget_data kbd
                            left join
                                account_analytic_account kp on kbd.account_analytic_id=kp.id
                            left join
                                account_budget_post abp on kbd.budget_id = abp.id
                            left join
                                kderp_budget_category bc on abp.budget_categ_id = bc.id
                            where
                                cat_code='material'
                            group by 
                                cat_code,account_analytic_id
                            union
                            Select 
                                account_analytic_id as id,
                                0 as material,
                                sum(coalesce(planned_amount,0)) as sub_contractor,
                                0 as site_expense,
                                0 as kinden_salary_admin_cost,
                                0 as bussiness_profit    
                            from 
                                kderp_budget_data kbd
                            left join
                                account_analytic_account kp on kbd.account_analytic_id=kp.id
                            left join
                                account_budget_post abp on kbd.budget_id = abp.id
                            left join
                                kderp_budget_category bc on abp.budget_categ_id = bc.id
                            where
                                cat_code='sub_contractor'
                            group by 
                                cat_code,account_analytic_id
                            union
                            Select 
                                account_analytic_id as id,
                                0 as material,
                                0 as sub_contractor,
                                sum(coalesce(planned_amount,0)) as site_expense,
                                0 as kinden_salary_admin_cost,
                                0 as bussiness_profit    
                            from 
                                kderp_budget_data kbd
                            left join
                                account_analytic_account kp on kbd.account_analytic_id=kp.id
                            left join
                                account_budget_post abp on kbd.budget_id = abp.id
                            left join
                                kderp_budget_category bc on abp.budget_categ_id = bc.id
                            where
                                cat_code='site_expense'
                            group by 
                                cat_code,account_analytic_id
                            union
                            Select 
                                account_analytic_id as id,
                                0 as material,
                                0 as sub_contractor,
                                0 as site_expense,
                                sum(coalesce(planned_amount,0)) as kinden_salary_admin_cost,
                                0 as bussiness_profit    
                            from 
                                kderp_budget_data kbd
                            left join
                                account_analytic_account kp on kbd.account_analytic_id=kp.id
                            left join
                                account_budget_post abp on kbd.budget_id = abp.id
                            left join
                                kderp_budget_category bc on abp.budget_categ_id = bc.id
                            where
                                cat_code='kinden_salary_admin_cost'
                            group by 
                                cat_code,account_analytic_id
                            union
                            Select 
                                account_analytic_id as id,
                                0 as material,
                                0 as sub_contractor,
                                0 as site_expense,
                                0 as kinden_salary_admin_cost,
                                sum(coalesce(planned_amount,0)) as bussiness_profit    
                            from 
                                kderp_budget_data kbd
                            left join
                                account_analytic_account kp on kbd.account_analytic_id=kp.id
                            left join
                                account_budget_post abp on kbd.budget_id = abp.id
                            left join
                                kderp_budget_category bc on abp.budget_categ_id = bc.id
                            where
                                cat_code='bussiness_profit'
                            group by 
                                cat_code,account_analytic_id) vwtemp group by id""")
kderp_total_budget_cat()

class kderp_budget_history(osv.osv):
    _name='kderp.budget.history'
    _description="KDERP Budget History"
    
    def create_history(self,cr,uid,job_id):            
            #cr.execute(" % prj_id)
            import datetime
            material = 0.0
            sub = 0.0
            site = 0.0
            admin =0.0
            profit = 0.0
            list_history = {'date':datetime.datetime.now().strftime('%Y-%m-%d'),
                            'status':'draft',
                            'material':0.0,
                            'sub_contractor':0.0,
                            'site_expense':0.0,
                            'kinden_salary_admin_cost':0.0,
                            'bussiness_profit':0.0,                  
                            'amount':0.0,
                            'account_analytic_id':job_id,
                            }
            cr.execute("""Select 
                            cat_code,
                            sum(coalesce(planned_amount,0)) as amount
                        from 
                            kderp_budget_data kbd
                        left join
                            account_analytic_account kp on kbd.account_analytic_id=kp.id
                        left join
                            account_budget_post abp on kbd.budget_id = abp.id
                        left join
                            kderp_budget_category bc on abp.budget_categ_id = bc.id
                        where
                            account_analytic_id in (%s)
                        group by cat_code""" % (job_id))
            
            for cat_code,amount in cr.fetchall():
                list_history[cat_code] = amount
                list_history['amount']+= amount
            new_id = self.create(cr,uid,list_history)
            return new_id
        
    _order = "date desc"
    
    _columns={
         'account_analytic_id':fields.many2one('account.analytic.account','Job',readonly=True,required=True),
         'status':fields.selection([('draft','Draft'),('accepted','Accepted'),('rejected','Rejected')],'Status'),     
         'date':fields.date('Date',required=True),
         'material':fields.float('Material'),
         'sub_contractor':fields.float('Sub-Contractor'),
         'site_expense':fields.float('Site-Expense'),
         'kinden_salary_admin_cost':fields.float("Salary, Admin. Cost"),
         'bussiness_profit':fields.float('Business Profit'),                  
         'amount':fields.float('Total')
         }
    _defaults={
            'status':lambda *x:'draft'
               }
kderp_budget_history()

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    
    _columns={
             'budget_total_cat_ids':fields.one2many('kderp.total.budget.cat','id','Budget Category Total',readonly="1"),
             'budget_history_ids':fields.one2many('kderp.budget.history','account_analytic_id','Budget History'),
             }
account_analytic_account()