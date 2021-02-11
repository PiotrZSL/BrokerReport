import investpy

__LOCAL_CURRENCY_CACHE = {}

def getCurrencyValue(name):
    global __LOCAL_CURRENCY_CACHE
    if name in __LOCAL_CURRENCY_CACHE:
        return __LOCAL_CURRENCY_CACHE[name]

    value =  Decimal(investpy.get_currency_cross_information('%s/PLN' % (name))['Bid'])
    __LOCAL_CURRENCY_CACHE[name] = value
    return value

__LOCAL_STOCK_CACHE = {}

def getStockValue(isin, name, exchange, currency):
    key = (isin, name, exchange, currency)
    if key in __LOCAL_STOCK_CACHE:
        return __LOCAL_STOCK_CACHE[key]


__LOCAL_STATIC_CACHE = []


def getStockStaticData(isin = None, currency = None):
    global __LOCAL_STATIC_CACHE

    if not __LOCAL_STATIC_CACHE:
        etfs = investpy.get_etfs_dict()
        for x in etfs:
            x['type'] = 'ETF'
        __LOCAL_STATIC_CACHE += etfs

        stocks = investpy.get_stocks_dict()
        for x in stocks:
            x['type'] = 'Equity'

        __LOCAL_STATIC_CACHE += stocks

        funds = investpy.get_funds_dict()
        for x in stocks:
            x['type'] = 'Fund'

        __LOCAL_STATIC_CACHE += funds

    # no country
    all_items = __LOCAL_STATIC_CACHE
    if isin:
        all_items = [x for x in all_items if x['isin'] == isin]

    if currency:
        all_items = [x for x in all_items if x['currency'] == currency]

    if all_items:
        return all_items[0]

    return None
