import requests
from decimal import Decimal
from datetime import date, timedelta
from Cache import CACHE

def getNBPValue(value, curency, time):
    if curency == 'PLN':
        return value
    
    global CACHE
    if 'NBP' not in CACHE:
        CACHE['NBP'] = {}
    
    if (curency, time) in CACHE['NBP']:
        return CACHE['NBP'][(curency, time)] * value
    
    ntime = time
    while True:
        try:
            data = requests.get("http://api.nbp.pl/api/exchangerates/rates/A/%s/%s?format=json" % (curency, ntime))
            data = Decimal(str(data.json()["rates"][0]["mid"]))
            CACHE['NBP'][(curency, time)] = data
            CACHE['NBP'][(curency, ntime)] = data
            return data * value
        except:
            d = date.fromisoformat(ntime) - timedelta(days = 1)
            ntime = d.isoformat()

def getNBPValueDayBefore(value, curency, time):
    return getNBPValue(value, curency, (date.fromisoformat(time) - timedelta(days = 1)).isoformat())

def getECBCurrencyTable(curency):
    data = requests.get("https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-%s.en.html" % (curency.lower())).content.decode()
    table = {}
    for x in data.split('chartData.push({ date: new Date(')[1:]:
        d = x.replace(')','').split(',', 3)
        d = date(int(d[0]), (int(d[1])+1), int(d[2]))
        v = Decimal(x.split('rate: ')[1].split(' ', 1)[0])
        table[d] = v
    start = min(table.keys())
    end = max(table.keys())
    value = table[start]
    while start != end:
        start += timedelta(days = 1)
        if start not in table:
            table[start] = value
        else:
            value = table[start]
    return table

def getECBValue(value, curency, time):
    if curency == 'PLN':
        return value

    global CACHE
    if 'ECB' not in CACHE:
        CACHE['ECB'] = {}

    if (curency, time) in CACHE['ECB']:
        return CACHE['ECB'][(curency, time)] * value


    pln = getECBCurrencyTable("PLN")
    cur = None
    if curency != "EUR":
        cur = getECBCurrencyTable(curency)

    for k,v in pln.items():
        if cur and k not in cur:
            continue
        cvalue = v if not cur else v/cur[k]
        CACHE['ECB'][(curency, k.isoformat())] = cvalue

    if (curency, time) not in CACHE['ECB']:
        raise Exception("Not supported conversion")

    return CACHE['ECB'][(curency, time)] * value

def getECBValueDayBefore(value, curency, time):
    return getECBValue(value, curency, (date.fromisoformat(time) - timedelta(days = 1)).isoformat())

def getPLNValueDayBefore(value, curency, time):
    return getNBPValueDayBefore(value, curency, time)
