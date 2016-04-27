# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp

#----------------------------------------------------------
# KDERP Price History - Estimation & Procurement using 
#----------------------------------------------------------
class product_product(osv.osv):
    """
    Inherit Product add new fields for 
    Estimation and Procurement Update and Using Price
    """
    
    _name = "product.product"
    _description = "KDERP Price History"    
    #_inherits = {'product.product': 'product_id'}
    
    _inherit = 'product.product'
    
    _columns = {        
        #'product_id': fields.many2one('product.product', 'Product', required=True, ondelete="cascade", select=True, track_visibility='onchange'),
        'master_list':fields.boolean('Master List?',track_visibility='onchange'),
        'date_updated':fields.date('Updated Date', track_visibility='onchange', required=True, readonly=True),
        'latest_date':fields.date('Last Purchase Date', readonly=True),
        
        #Price Area
        #Reference Price
        'ref_min':fields.float('Min Price', digits_compute=dp.get_precision('Amount'), readonly=True),
        'ref_avg':fields.float('AVG Price', digits_compute=dp.get_precision('Amount'), readonly=True),
        'ref_max':fields.float('Max Price', digits_compute=dp.get_precision('Amount'), readonly=True),
        'ref_latest':fields.float('Latest Price', digits_compute=dp.get_precision('Amount'), readonly=True),
        #Using Price
        'price':fields.float('Estimation Price', track_visibility='onchange'),
        #Warning Area
        'outofdate':fields.boolean('Out of date', readonly=1, help='Checked when Estimation Price not up-to-date, compare with day in settings'),
        'not_available':fields.boolean('N/A', readonly=1, help='Checked when this material never been purchased'),
        'different':fields.boolean('Having gap', readonly=1, help='Checked when this Estimation having gap larger than Price depended type of price and rate in settings'),
        
    }
    _defaults = {        
    }
      
    def init(self, cr):
        cr.execute("""CREATE OR REPLACE FUNCTION KDERPFN_UPDATED_DATE_PRICE()
                        RETURNS TRIGGER AS
                     $BODY$
                            DECLARE
                                TYPE_PRICE TEXT;
                     DIFF_VALUE NUMERIC;
                            BEGIN
                                SELECT BASEON_TYPEPRICE INTO TYPE_PRICE FROM RES_COMPANY LIMIT 1;
                                SELECT PRICE_DIFFERENT INTO DIFF_VALUE FROM RES_COMPANY LIMIT 1;
                                -- When Update Price trigger update outofdate and not_availble
                                IF (TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND COALESCE(NEW.PRICE, 0)!=COALESCE(OLD.PRICE, 0))) THEN
                                    UPDATE PRODUCT_PRODUCT SET 
                                                                DATE_UPDATED = NOW(),
                                                                OUTOFDATE=FALSE,
                                                                NOT_AVAILABLE=CASE WHEN COALESCE(NEW.PRICE,0)=0 THEN TRUE ELSE FALSE END 
                                    WHERE ID = NEW.ID;
                                END IF;
                                -- When Update Price (AVG, MAX, MIN) trigger update different
                                IF (
                                        TG_OP = 'UPDATE' AND 
                                        (    COALESCE(NEW.REF_AVG, 0)!=COALESCE(OLD.REF_AVG, 0) OR 
                                            COALESCE(NEW.REF_MIN, 0)!=COALESCE(OLD.REF_MIN, 0) OR 
                                            COALESCE(NEW.REF_MAX, 0)!=COALESCE(OLD.REF_MAX, 0) OR
                                            COALESCE(NEW.PRICE, 0)!=COALESCE(OLD.PRICE, 0)
                                        )
                                    ) 
                                THEN
                                    UPDATE PRODUCT_PRODUCT SET 
                                                            DIFFERENT=
                                                                        CASE WHEN COALESCE(NEW.PRICE,0)=0 THEN FALSE 
                                                                        ELSE
                                                                            ABS((CASE WHEN TYPE_PRICE='REF_MIN' THEN NEW.REF_MIN 
                                                                                ELSE
                                                                                    CASE WHEN TYPE_PRICE='REF_MAX' THEN NEW.REF_MAX
                                                                                    ELSE
                                                                                        CASE WHEN TYPE_PRICE='REF_LATEST' THEN NEW.REF_LATEST
                                                                                        ELSE                                                                                            
                                                                                            NEW.REF_AVG
                                                                                        END
                                                                                    END
                                                                                END)
                                                                                -NEW.PRICE)/NEW.PRICE*100.0>=DIFF_VALUE
                                                                        END
                                    WHERE
                                        ID = NEW.ID;
                                END IF;
                                RETURN NEW;
                            END;
                        $BODY$
                    LANGUAGE PLPGSQL VOLATILE
                    COST 100;
                    
                    DROP TRIGGER IF EXISTS KDERPTRG_UPDATED_PRICE ON PRODUCT_PRODUCT;
                    CREATE TRIGGER KDERPTRG_UPDATED_PRICE
                        AFTER INSERT OR UPDATE
                        ON PRODUCT_PRODUCT
                        FOR EACH ROW
                        EXECUTE PROCEDURE KDERPFN_UPDATED_DATE_PRICE();""")
product_product()
