from enum import Enum
from Exchanges import findExchange
from InfoProvider import getStockStaticData 
import pycountry
import gettext

class Asset:
    def __init__(self, ticker, name):
        self.ticker = ticker
        self.name = name

    @property
    def country(self):
        return None

    def __str__(self):
        return str(self.ticker)

    def __eq__(self, other):
        return type(self) == type(other) and self.ticker == other.ticker;

    def __hash__(self):
        return hash(type(self)) + hash(self.ticker)

class Currency(Asset):
    def __init__(self, ticker, name):
        super().__init__(ticker, name)

    @property
    def type(self):
        return "Currency"

class Stock(Asset):
    def __init__(self, isin, ticker, exchange, currency, name):
        super().__init__(ticker, name)
        self.isin = isin
        self.exchange = exchange
        self.currency = currency
        self._type = 'Equity'

    @property
    def country(self):
        return self.exchange.iso if self.exchange and self.exchange.iso else None
    
    @property
    def type(self):
        return self._type
    
    def __eq__(self, other):
        return type(self) == type(other) and self.ticker == other.ticker and self.exchange == other.exchange and self.currency == other.currency

    def __hash__(self):
        return hash(type(self)) + hash(self.ticker) + hash(self.exchange) + hash(self.currency)
    
    def __str__(self):
        return str(self.ticker) if not self.exchange else "%s.%s" % (str(self.ticker), self.exchange)

class AssetDatabase:
    def __init__(self):
        self._currency = {}
        self._stocks = []
        self._changes = {}

    def updateData(self):
        for x in self._stocks:
            if x.exchange and isinstance(x.exchange, str):
                x.exchange = findExchange(x.exchange)

        for x in self._stocks:
            if not x.isin:
                continue

            data = getStockStaticData(x.isin, x.currency)
            if data:
                x.name = data['name']
                x._type = data['type']

    def getCurrency(self, ticker):
        if ticker in self._currency:
            return self._currency[ticker]

        name = ticker
        try:
            pl = gettext.translation('iso4217', pycountry.LOCALES_DIR, languages=['pl'])
            name = pycountry.currencies.lookup(ticker).name
        except:
            return None

        c = Currency(ticker, name)
        self._currency[c.ticker] = c
        return c

    def getStock(self, isin = None, ticker = None, exchange = None, currency = None, name = None):
        t = ticker
        e = exchange

        while t and e and (t, e) in self._changes:
            w = self._changes[(t, e)]
            t = w[0]
            e = w[1]

        for s in self._stocks:
            if isin and s.isin and s.isin != isin:
                continue

            if t and s.ticker and s.ticker != t:
                continue

            if e and s.exchange and e != s.exchange:
                continue

            if currency and s.currency and currency != s.currency:
                continue

            if name and s.name and name != s.name:
                continue

            if isin and not s.isin:
                s.isin = isin

            if t and not s.ticker:
                s.ticker = t

            if e and not s.exchange:
                s.exchange = e

            if currency and not s.currency:
                s.currency = currency

            if name and not s.name:
                s.name = name

            return s

        s = Stock(isin, ticker, e, currency, name)
        self._stocks.append(s)
        return s

    def changeName(self, oldTicker, oldExchange, newTicker, newExchange):
        oldE = oldExchange
        newE = newExchange
        
        for x in self._stocks:
            if x.ticker == oldTicker and x.exchange:
                x.ticker = newTicker
                x.exchange = newE
                break

        self._changes[(oldTicker, oldE)] = (newTicker, newE)

