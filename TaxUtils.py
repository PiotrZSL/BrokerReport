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
            data = Decimal(data.json()["rates"][0]["mid"])
            CACHE['NBP'][(curency, time)] = data
            CACHE['NBP'][(curency, ntime)] = data
            return data * value
        except:
            d = date.fromisoformat(ntime) - timedelta(days = 1)
            ntime = d.isoformat()
