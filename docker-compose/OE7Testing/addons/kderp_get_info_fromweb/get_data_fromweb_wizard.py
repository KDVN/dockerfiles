from openerp.osv import osv, fields
#from osv.orm import intersect
#from openerp import tools

class get_data_fromweb_wizard(osv.TransientModel):
    """
    Wizard ho tro tim kiem va update du lieu cac cong ty
    tu trang web cua GDT
    """
    _name = 'get.data.fromweb.wizard'
    _description = 'Get Data From Web Search'
    
    def query_data_from_gdt(self, cr, uid, ids, context):
        """
        Su dung lib request de lay du lieu
        requests, BeautifulSoup
        apt-get install python-requests
        argument page su dung de lam deep search
        """
        import requests
        from bs4 import BeautifulSoup
        result = {'tax_code':'','name':'','address':'','status':''}
        page = 1
        do_query = True
        ij=1400
        fo = open("/home/develop/Listlinks.html",'w')
        fo1 = open("/home/develop/Listlinked.html",'w')
        while ij<=7160:
            url = 'http://nhaccachmang.net/forum/index.php?showtopic=2382&st=%s'            
            query = ij
            fo1.write(url % query)
            fo1.write("\n")
            req = requests.get(url % query)           
            raw_data = req.text
            raw_html = BeautifulSoup(raw_data)
            for link in raw_html.find_all('a'):
                if link.get('href'):
                    new_link=str(link.get('href').encode('ascii','ignore'))                
                    if new_link.find('mediafire')>=0:
                        new_link=new_link.replace('listen','download')
                        fo.write("\n")                
                        fo.write(new_link)
            ij=ij+20                
        fo.close()
        fo1.close()      
        return True
get_data_fromweb_wizard()  