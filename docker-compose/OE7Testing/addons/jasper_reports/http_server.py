from service.http_server import *
from BaseHTTPServer import BaseHTTPRequestHandler
import netsvc
import tools

class Message:
    def __init__(self):
        self.status = False


class JasperHandler(BaseHTTPRequestHandler):
    cache = {}
    rotocol_version = 'HTTP/1.1'
    _HTTP_OPTIONS= { 'DAV' : ['1', '2'],
                    'Allow' : [ 'GET', 'HEAD', 'COPY', 'MOVE', 'POST', 'PUT',
                            'PROPFIND', 'PROPPATCH', 'OPTIONS', 'MKCOL',
                            'DELETE', 'TRACE', 'REPORT', ]
                    }
    def get_db_from_path(self, uri):
        # interface class will handle all cases.
        res =  self.IFACE_CLASS.get_db(uri, allow_last=True)
        return res
    
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        self.setup()
        if hasattr(self, '_init_buffer'):
            self._init_buffer()
            
    def handle(self):
        """Handle multiple requests if necessary."""
        self.close_connection = 1
        try:
            self.handle_one_request()
            while not self.close_connection:
                self.handle_one_request()
        except Exception as e:
            try:
                self.log_error("Request timed out: %r \n Trying old version of HTTPServer", e)
                self._init_buffer()
            except Exception as e:
                #a read or a write timed out.  Discard this connection
                self.log_error("Not working neither, closing connection\n %r", e)
                self.close_connection = 1
                
    def __init__(self, request, client_address, server):
        pass
        #print "REQUEST: ", dir(request)
        #print "DIR SELF: ", dir(self)

    #def __getattr__(self, name):
        #print "NAME: ", name
        #return JasperHandler.__getattr__(self, name)

    def _prep_OPTIONS(self, opts):
        ret = opts
        dc=self.IFACE_CLASS
        uri=urlparse.urljoin(self.get_baseuri(dc), self.path)
        uri=urllib.unquote(uri)
        try:
            ret = dc.prep_http_options(uri, opts)
        except DAV_Error, (ec,dd):
            pass
        except Exception,e:
            self.log_error("Error at options: %s", str(e))
            raise
        return ret

    def parse_request(self, *args, **kwargs):
        #self.headers = Message()
        #self.request_version = 'HTTP/1.1'
        #self.command = 'OPTIONS'

        path = self.raw_requestline.replace('GET','').strip().split(' ')[0]
        try:
            result = self.execute(path)
        except Exception, e:
            result = '<error><exception>%s</exception></error>' % (e.args, )
        self.wfile.write( result )
        return True

    def execute(self, path):
        #print "PATH: ", path
        path = path.strip('/')
        path = path.split('?')
        model = path[0]
        arguments = {}
        for argument in path[-1].split('&'):
            argument = argument.split('=')
            arguments[ argument[0] ] = argument[-1]

        use_cache = tools.config.get('jasper_cache', True)
        database = arguments.get('database', tools.config.get('jasper_database', 'demo') )
        user = arguments.get('user', tools.config.get('jasper_user', 'admin') )
        password = arguments.get('password', tools.config.get('jasper_password', 'admin') )
        depth = int( arguments.get('depth', tools.config.get('jasper_depth', 3) ) )
        language = arguments.get('language', tools.config.get('jasper_language', 'en'))

        # Check if data is in cache already
        key = '%s|%s|%s|%s|%s' % (model, database, user, depth, language)
        if key in self.cache:
            return self.cache[key]

        context = {
            'lang': language,
        }

        uid = netsvc.dispatch_rpc('common', 'login', (database, user, password))
        result = netsvc.dispatch_rpc('object', 'execute', (database, uid, password, 'ir.actions.report.xml', 'create_xml', model, depth, context))

        if use_cache:
            self.cache[key] = result

        return result
from openerp.service.http_server import reg_http_service,OpenERPAuthProvider
reg_http_service('/jasper/', JasperHandler)
