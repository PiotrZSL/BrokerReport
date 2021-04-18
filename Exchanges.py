from ImportUtils import getCsv
import os

QUICK_MAP={'WWA':'XWAR',
           'NDQ':'NASDAQ',
           'MICEX':'MISX',
           'ARCA':'ARCX',
           'TMX':'XTSX'}

class Exchange:
    def __init__(self, country, iso, code):
        self.country = country
        self.iso = iso
        self.code = code

    def __str__(self):
        return self.code

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other):
        return self.code == other.code

    def __ne__(self, other):
        return self.code != other.code

__EX_CACHE_CSV = None
__EX_CACHE = {}

def findExchange(code):
    global __EX_CACHE_CSV
    global __EX_CACHE

    if code in QUICK_MAP:
        return findExchange(QUICK_MAP[code])

    if not __EX_CACHE_CSV:
        __EX_CACHE_CSV = getCsv(os.path.join(os.path.dirname(__file__), "data", "ISO10383_MIC.csv"), delimiter=',')

    ucode = code.upper()
    if ucode in __EX_CACHE:
        return __EX_CACHE[ucode]

    for it in __EX_CACHE_CSV:
        if ucode == it['MIC']:
            e = Exchange(it["COUNTRY"].title(), it["ISO COUNTRY CODE (ISO 3166)"], it["OPERATING MIC"])
            __EX_CACHE[ucode] = e
            return e
    
    for it in __EX_CACHE_CSV:
        if ucode == it["ACRONYM"]:
            e = Exchange(it["COUNTRY"].title(), it["ISO COUNTRY CODE (ISO 3166)"], it["OPERATING MIC"])
            __EX_CACHE[ucode] = e
            return e
    
    for it in __EX_CACHE_CSV:
        if ucode == it["OPERATING MIC"]:
            e = Exchange(it["COUNTRY"].title(), it["ISO COUNTRY CODE (ISO 3166)"], it["OPERATING MIC"])
            __EX_CACHE[ucode] = e
            return e

    raise Exception("Exchange %s not found, add mapping manually" % (code))
