import requests
from decimal import Decimal
from datetime import date, timedelta

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
            data = requests.get("http://api.nbp.pl/api/exchangerates/rates/A/%s/%s?format=json" % (curency, ntime))
            data = Decimal(data.json()["rates"][0]["mid"])
            NBP_CACHE[(curency, time)] = data
            NBP_CACHE[(curency, ntime)] = data
            return data * value
        except Exception as e:
            d = date.fromisoformat(ntime) - timedelta(days = 1)
            ntime = d.isoformat()
