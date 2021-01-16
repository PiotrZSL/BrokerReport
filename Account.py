from sortedcontainers import SortedList
from collections import defaultdict
from decimal import Decimal
from Action import EActionType
from Asset import *

class Account:
    def __init__(self, name, broker):
        self._name = name
        self._broker = broker
        self._assets = AssetDatabase()
        self._actions = SortedList(key=lambda x : x.time)

    def _finishImport(self):
        self._assets.updateExchange()

    def currency(self, *args, **kwarg):
        return self._assets.getCurrency(*args, **kwarg)

    def stock(self, *args, **kwarg):
        return self._assets.getStock(*args, **kwarg)
    
    @property
    def broker(self):
        return self._broker

    @property
    def name(self):
        return self._name

    @property
    def actions(self):
        return self._actions

    def dump(self):
        print("Account: %s/%s" % (self._broker, self._name))
        for x in self._actions:
            x.dump();
    
    def _add(self, action):
        self._actions.add(action)

    @property
    def assets(self):
        result = defaultdict(lambda : [Decimal(0), None])
        actions = sum([[x] + x.flat_actions for x in self._actions], []) 
        for action in actions:
            if action.type != EActionType.DIVIDEND:
                result[action.asset][0] += action.count
                result[action.asset][1] = action.time
        result = [(x, y[0], y[1]) for x, y in result.items() if not y[0].is_zero()]
        result.sort(key=lambda x : (x[0].type, x[2]))
        return result

    def _split(self, asset, date, value):
        for x in self._actions:
            if x.asset == asset and x.time <= date:
                x.split(value)
