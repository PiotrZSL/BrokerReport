import requests
from decimal import Decimal

NBP_CACHE={}

def getNBPValue(value, curency, time):
    if curency == 'PLN':
        return value
    
    global NBP_CACHE
    if (curency, time) in NBP_CACHE:
        return NBP_CACHE[(curency, time)] * value
    
    ntime = time
    while True:
        try:
            data = Decimal(requests.get("http://api.nbp.pl/api/exchangerates/rates/A/%s/%s?format=json" % (curency, ntime)).json()["rates"][0]["mid"])
            NBP_CACHE[(curency, time)] = data
            NBP_CACHE[(curency, ntime)] = data
            return data * value
        except:
            d = date.fromisoformat(ntime) - timedelta(days = 1)
            ntime = d.isoformat()
