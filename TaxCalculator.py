from Action import *
from Asset import *
from TaxUtils import getNBPValue
from decimal import Decimal
from collections import defaultdict
from copy import copy

#Tax FIFO calculator

class TaxCalculator:
    def __init__(self, account):
        self._account = account
        self._actions = account.actions
        self._assets = defaultdict(list)

    def visitBuy(self, action):
        if type(action.asset) is Currency:
            return

        actions = [x for x in action.flat_actions if not x.actions]
        data = [copy(action.count), action.count, [ (getNBPValue(x.count, x.asset.ticker, x.time.date().isoformat()), x) for x in actions ]]
        self._assets[action.asset].append(data)

    def visitSell(self, action):
        if type(action.asset) is Currency:
            return

        data = self._assets[action.asset]

        count = action.count * Decimal(-1)
        while not count.is_zero():
            if not data:
                raise Exception("Missing assets on sell - shorting not supported yet")
            
            selected = count if count <= data[0][0] else data[0][0]
            precent = selected / data[0][1]
            for pln, act in data[0][2]:
                act.addTaxCalculation(action, pln*precent)
            count -= selected
            data[0][0] -= selected
            if data[0][0].is_zero():
                del data[0]

        actions = [x for x in action.flat_actions if not x.actions]
        for pln, act in [ (getNBPValue(x.count, x.asset.ticker, x.time.date().isoformat()), x) for x in actions ]:
            act.addTaxCalculation(action, pln)

    def calculate(self):
        for action in self._actions:
            if action.type == EActionType.BUY:
                self.visitBuy(action)
                continue
            
            if action.type == EActionType.SELL:
                self.visitSell(action)
                continue

