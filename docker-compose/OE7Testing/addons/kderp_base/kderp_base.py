from _socket import timeout
def diff_month(date_from, date_to):
    return (date_to.year - date_from.year)*12 + date_to.month - date_from.month                                                                             

def round_base(x, base=5):
        from openerp.tools.float_utils import float_round as round
        return round(x, base)
    
def get_new_from_tree( cr, uid, id, object, lists, field, startnum=1, step_num=1, context={}):
    res = 0
    list_delete=[]
    #list_new_update=[]
    list_nochange=[]
    list_delete = [0]
    lists_remain = []
    for lst in lists:
        if lst[0] in (2,3,5): #Delete Cut Link
            list_delete.append(lst[1])
        elif lst[0]==4:
            list_nochange.append(lst[1])
        elif lst[0]==1:
            if field not in lst[2]:
                list_nochange.append(lst[1])
            else:
                lists_remain.append(lst)
        else:
            lists_remain.append(lst)
            
    max_sq=startnum - step_num
    for lst in lists_remain:
        if max_sq<lst[2][field]:
            max_sq = lst[2][field]
    if id:
        object_name = object.__class__.__name__
        try:
            table_name = object._table_name
        except:
            table_name = object_name.replace('.','_')
        res_ids = False
        if list_nochange:
            res_ids = ",".join(map(str,list_nochange))
        
        except_ids = ",".join(map(str,list_delete))
        
        if res_ids:
            cr.execute("""Select max(%s) from %s where id not in (%s) and id in (%s)""" % (field,table_name,except_ids,res_ids))
            exist_max_val = cr.fetchone()[0]
        else:
            exist_max_val = 0
        
        if max_sq<exist_max_val:
            max_sq = exist_max_val
    res = max_sq+step_num
    return res

def get_new_value_from_tree( cr, uid, id, object, lists, field, context={}): 
    list_nochange=[]
    list_delete = [0]
    lists_remain = []
    res = False
    for lst in lists:
        if lst[0] in (2,3,5): #Delete Cut Link
            list_delete.append(lst[1])
        elif lst[0]==4:
            list_nochange.append(lst[1])
        elif lst[0]==1:
            if field not in lst[2]:
                list_nochange.append(lst[1])
            else:
                lists_remain.append(lst)
        else:
            lists_remain.append(lst)
            
    for lst in lists_remain:        
        res = lst[2][field]
        
    if id and not res:
        object_name = object.__class__.__name__
        try:
            table_name = object._table_name
        except:
            table_name = object_name.replace('.','_')
            
        res_id = max(list_nochange) if list_nochange else False         
        
        if res_id:
            cr.execute("""Select %s from %s where id = %s""" % (field,table_name,res_id))
            res = cr.fetchone()[0]            
            
    return res

def check_connection(server = '192.168.1.11', port = '5432', timeout = 5):
    """
        (server, port, timeout) -> Boolean
    """
    import socket    
    #Simply change the host and port values
    host = server
    port = port
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.shutdown(2)
        return True
    except:
        return False