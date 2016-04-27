# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

#-------------------------------------------------------------
#Indonesian
##### License from http://riri.blogdetik.com/2009/02/23/php-convertion-number-to-words-indonesian/ by Riri
#-------------------------------------------------------------
indo_array = ["Satu","Dua","Tiga","Empat","Lima","Enam","Tujuh","Delapan","Sembilan"]
import re
def amount_to_text_in(num,curr='Rupiah',reserve=False,recursive=False):
    
    res = ""
    #1. Ratusan Juta (Kuadran I) - Hundred Millenium
    num = int(num)
    kw1 = int(num/1000000.0)
    num = num - kw1*1000000
    if (kw1>0):
        res = res + amount_to_text_in(kw1,'',False,True) + " Juta "
    
    #2. Jutaan (Kuadran II ) -  Millenium
    kw2 = int(num/1000.0)
    num = num - kw2 *1000
    if (kw2>0):
        res = res + amount_to_text_in(kw2,'',False,True) + " Ribu "
    
    ratus = int(num/100.0)
    num = num - ratus*100
    if (ratus):
        if (ratus-1)>=0 and (ratus-1)<len(indo_array):
            ratus = indo_array[ratus-1]
        else:
            ratus = ""
        res = res + ratus + " Ratus "

    #B. cari bahasa puluhan - Tens
    puluh = int(num/10.0)
    num = num - puluh*10
    if (puluh):
        if (puluh>1):
            puluh = indo_array[puluh-1]
            res = res + puluh + " Puluh "
        else:
            ada = 0
            if (num-1)>=0 and (num-1)<len(indo_array):
                satuan = indo_array [num-1]    
            else:
                satuan = ""
            res = res + satuan + " belas "
    #C. cari bahasa satuan - Unit
    sat = num
    if (puluh or sat):
        if (res):
            res = res + " "
        if puluh<2 or type(puluh)==type('satus'):
            try:
                if (puluh*10+sat-1)>=0 and (puluh*10+sat-1)<len(indo_array):
                    res = res + indo_array[puluh*10 + sat -1]                
            except:
                if (sat-1)>=0 and (sat-1)<len(indo_array):
                    #try:
                    res = res + indo_array[sat -1]
                    #except:
                       # pass
        else:
            try:
                if (puluh-1)>=0 or (puluh-1)<len(indo_array):
                    res = res + indo_array[puluh-1] + " belas "
            except:
                res = res + " belas "
            if (sat):
                if (sat-1)>=0 and (sat-1)<len(indo_array):
                    res = res + "-" + indo_arramount_to_text_inay[sat-1]

    res = res.replace("belas","Sepuluh")
    res = res.replace("satu belas","Sebelas")
    res = res.replace("satu ratus", "Seratus")
    res = res.replace("satu ribu", "Seribu")
    res = re.sub(' +',' ',res)
    if not recursive:
        if reserve:
            res = curr + " " + res
        else:
            res = res + " "  + curr 
    return res

#-------------------------------------------------------------
#Vietnamese
#-------------------------------------------------------------
#from tools.translate import _

to_19_vn = ( u'không', u'một', u'hai', u'ba', u'bốn', u'năm', u'sáu',
          u'bảy', u'tám', u'chín', u'mười', u'mười một', u'mười hai', u'mười ba',
          u'mười bốn', u'mười lăm', u'mười sáu', u'mười bảy', u'mười tám', u'mười chín' )

tens_vn  = ( u'hai mươi', u'ba mươi', u'bốn mươi', u'năm mươi', u'sáu mươi', u'bảy mươi', u'tám mươi', u'chín mươi')

denom_vn = ( '',u'nghìn', u'triệu', u'tỷ', u'nghìn tỷ', u'trăm nghìn tỷ',
          'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
          'Decillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
          'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion' )

# convert a value < 100 to English.
def _convert_nn_vn(val):
    if val < 20:
        return to_19_vn[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_vn)):
        if dval + 10 > val:
            if val % 10:
                a = u'lăm'
#                if to_19_vn[val % 10] == u'năm':
#                    a = u'lăm'
                if to_19_vn[val % 10] == u'một':
                    a = u'mốt'
                else:
                    a = to_19_vn[val % 10]
                return dcap + ' ' + a
            return dcap

# convert a value < 1000 to english, special cased because it is the level that kicks 
# off the < 100 special case.  The rest are more general.  This also allows you to
# get strings in the form of 'forty-five hundred' if called directly.
def _convert_nnn_vn(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19_vn[rem] + u' trăm'
        if (mod>0 and mod <10):
            word = word + u' lẻ '
        elif mod>0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn_vn(mod)
    return word

def vietnam_number(val):
    if val < 100:
        return _convert_nn_vn(val)
    if val < 1000:
         return _convert_nnn_vn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_vn))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn_vn(l) + ' ' + denom_vn[didx]
            if r > 0:
                ret = ret + ', ' + vietnam_number(r)
            return ret

def amount_to_text_vn(number,curr='đồng',reserve=False,decimal=False):
    number = '%.2f' % number
    list = str(number).split('.')
    start_word = vietnam_number(int(list[0]))
    if int(list[1])>0:
        end_word = vietnam_number(int(list[1]))
    #cents_number = int(list[1])
        if decimal:
            final_result = start_word + curr + u' và ' + end_word + ' %s' % decimal
        else:
            final_result = start_word + u' phẩy ' + end_word + curr
    else:
        final_result = start_word  + curr + u" chẵn"
    return final_result
#-------------------------------------------------------------
#ENGLISH
#-------------------------------------------------------------
try:
    from tools.translate import _
except:
    from openerp.tools.translate import _

to_19 = ( 'Zero',  'One',   'Two',  'Three', 'Four',   'Five',   'Six',
          'Seven', 'Eight', 'Nine', 'Ten',   'Eleven', 'Twelve', 'Thirteen',
          'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen' )
tens  = ( 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
denom = ( '',
          'Thousand',     'Million',         'Billion',       'Trillion',       'Quadrillion',
          'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
          'Decillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
          'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion' )

# convert a value < 100 to English.
def _convert_nn(val):
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19[val % 10]
            return dcap

# convert a value < 1000 to english, special cased because it is the level that kicks 
# off the < 100 special case.  The rest are more general.  This also allows you to
# get strings in the form of 'forty-five hundred' if called directly.
def _convert_nnn(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19[rem] + ' Hundred'
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn(mod)
    return word

def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
         return _convert_nnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ' ' + english_number(r)
            return ret

def amount_to_text_en(number, currency,reserve=False):
    number = '%.2f' % number
    units_name = currency or ""
    list = str(number).split('.')
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    cents_name = (cents_number > 1) and 'Cents' or 'Cent'
    if (cents_number>0):
        end_words = ' and ' + str.lower(end_word) +' '+str.lower(cents_name)
    else:
        end_words = " only"
        
    if reserve:
        final_result = units_name + " " + str.lower(start_word) + end_words
    else:
        final_result = str.lower(start_word) +' '+ units_name + end_words  
    return final_result


#-------------------------------------------------------------
# French
#-------------------------------------------------------------

unites = {
    0: '', 1:'un', 2:'deux', 3:'trois', 4:'quatre', 5:'cinq', 6:'six', 7:'sept', 8:'huit', 9:'neuf',
    10:'dix', 11:'onze', 12:'douze', 13:'treize', 14:'quatorze', 15:'quinze', 16:'seize',
    21:'vingt et un', 31:'trente et un', 41:'quarante et un', 51:'cinquante et un', 61:'soixante et un',
    71:'septante et un', 91:'nonante et un', 80:'quatre-vingts'
}

dizaine = {
    1: 'dix', 2:'vingt', 3:'trente',4:'quarante', 5:'cinquante', 6:'soixante', 7:'septante', 8:'quatre-vingt', 9:'nonante'
}

centaine = {
    0:'', 1: 'cent', 2:'deux cent', 3:'trois cent',4:'quatre cent', 5:'cinq cent', 6:'six cent', 7:'sept cent', 8:'huit cent', 9:'neuf cent'
}

mille = {
    0:'', 1:'mille'
}

def _100_to_text_fr(chiffre):
    if chiffre in unites:
        return unites[chiffre]
    else:
        if chiffre%10>0:
            return dizaine[chiffre / 10]+'-'+unites[chiffre % 10]
        else:
            return dizaine[chiffre / 10]

def _1000_to_text_fr(chiffre):
    d = _100_to_text_fr(chiffre % 100)
    d2 = chiffre/100
    if d2>0 and d:
        return centaine[d2]+' '+d
    elif d2>1 and not(d):
        return centaine[d2]+'s'
    else:
        return centaine[d2] or d

def _10000_to_text_fr(chiffre):
    if chiffre==0:
        return 'zero'
    part1 = _1000_to_text_fr(chiffre % 1000)
    part2 = mille.get(chiffre / 1000,  _1000_to_text_fr(chiffre / 1000)+' mille')
    if part2 and part1:
        part1 = ' '+part1
    return part2+part1
    
def amount_to_text_fr(number, currency):
    units_number = int(number)
    units_name = currency
    if units_number > 1:
        units_name += 's'
    units = _10000_to_text_fr(units_number)
    units = units_number and '%s %s' % (units, units_name) or ''
    
    cents_number = int(number * 100) % 100
    cents_name = (cents_number > 1) and 'cents' or 'cent'
    cents = _100_to_text_fr(cents_number)
    cents = cents_number and '%s %s' % (cents, cents_name) or ''
    
    if units and cents:
        cents = ' '+cents
        
    return units + cents

#-------------------------------------------------------------
# Dutch
#-------------------------------------------------------------

units_nl = {
    0:'', 1:'een', 2:'twee', 3:'drie', 4:'vier', 5:'vijf', 6:'zes', 7:'zeven', 8:'acht', 9:'negen',
    10:'tien', 11:'elf', 12:'twaalf', 13:'dertien', 14:'veertien' 
}

tens_nl = {
    1: 'tien', 2:'twintig', 3:'dertig',4:'veertig', 5:'vijftig', 6:'zestig', 7:'zeventig', 8:'tachtig', 9:'negentig'
}

hundreds_nl = {
    0:'', 1: 'honderd', 
}

thousands_nl = {
    0:'', 1:'duizend'
}

def _100_to_text_nl(number):
    if number in units_nl:
        return units_nl[number]
    else:
        if number%10 > 0:
            if number>10 and number<20:
                return units_nl[number % 10]+tens_nl[number / 10]
            else:
                units = units_nl[number % 10]
                if units[-1] == 'e':
                    joinword = 'ën'
                else:
                    joinword = 'en'
                return units+joinword+tens_nl[number / 10]
        else:
            return tens_nl[number / 10]

def _1000_to_text_nl(number):
    part1 = _100_to_text_nl(number % 100)
    part2 = hundreds_nl.get(number / 100, units_nl[number/100] + hundreds_nl[1])
    if part2 and part1:
        part1 = ' ' + part1
    return part2 + part1

def _10000_to_text_nl(number):
    if number==0:
        return 'nul'
    part1 = _1000_to_text_nl(number % 1000)
    if thousands_nl.has_key(number / 1000):
        part2 = thousands_nl[number / 1000]
    else:
        if (number / 1000 % 100 > 0) and (number / 1000 > 100):
            space = ' '
        else:
            space = ''
        part2 = _1000_to_text_nl(number / 1000) + space + thousands_nl[1]
    if part2 and part1:
        part1 = ' ' + part1
    return part2 + part1
    
def amount_to_text_nl(number, currency,reserve=False):
    units_number = int(number)
    units_name = currency
    units = _10000_to_text_nl(units_number)
    units = units_number and '%s %s' % (units, units_name) or ''
    
    cents_number = int(number * 100) % 100
    cents_name = 'cent'
    cents = _100_to_text_nl(cents_number)
    cents = cents_number and '%s %s' % (cents, cents_name) or ''

    if units and cents:
        cents = ' ' + cents
        
    return units + cents

#-------------------------------------------------------------
# Generic functions
#-------------------------------------------------------------

_translate_funcs = {'fr' : amount_to_text_fr, 'nl' : amount_to_text_nl,'en' : amount_to_text_en,
                    'vn' : amount_to_text_vn,'in':amount_to_text_in}

def add_amount_to_text_function(lang, func):
    _translate_funcs[lang] = func
    
#TODO: we should use the country AND language (ex: septante VS soixante dix)
#TODO: we should use en by default, but the translation func is yet to be implemented
def amount_to_text(nbr, lang='fr', currency='euro',reserve=False,decimal=False):
    """
    Converts an integer to its textual representation, using the language set in the context if any.
    Example:
        1654: mille six cent cinquante-quatre.
    """
    
    if not _translate_funcs.has_key(lang):
#TODO: use logger   
        print "WARNING: no translation function found for lang: '%s'" % (lang,)
#TODO: (default should be en) same as above
        lang = 'fr'
    if decimal:
        return _translate_funcs[lang](nbr, currency,reserve,decimal)
    else:
        return _translate_funcs[lang](nbr, currency,reserve)

if __name__=='__main__':
    from sys import argv
    
    lang = 'nl'
    if len(argv) < 2:
        for i in range(1,200):
            print i, ">>", amount_to_text(i, lang)
        for i in range(200,999999,139):
            print i, ">>", amount_to_text(i, lang)
    else:
        print amount_to_text(int(argv[1]), lang)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: