from enum import Enum
from sortedcontainers import SortedList
from collections import defaultdict
from decimal import Decimal

class EActionType(Enum):
    SEND = 1
    RECEIVE = 2
    BUY = 3
    SELL = 4
    FEE = 5
    TAX = 6
    DIVIDEND = 7
    FOREX = 8
    PAYMENT = 9
    INCOME = 10

class Action:
    def __init__(self, time, actionType, count, asset, percent = None):
        self._time = time
        self._actionType = actionType
        self._count = count
        self._asset = asset
        self._percent = percent
        self._parent = None
        self._actions = SortedList(key=lambda x : x.time)
        self._taxCalculations = []

    @property
    def time(self):
        return self._time

    @property
    def type(self):
        return self._actionType

    @property
    def count(self):
        return self._count

    @property
    def asset(self):
        return self._asset

    @property
    def parent(self):
        return self._parent

    @property
    def tax_calculations(self):
        return self._taxCalculations

    @property
    def tax(self):
        result = defaultdict(lambda : [Decimal(0), Decimal(0)])
        for action, value in self._taxCalculations:
            action.time.year
            if value >= Decimal(0):
                result[action.time.year][1] += value
            else:
                result[action.time.year][0] += value
        return result

    @property
    def flat_tax(self):
        result = defaultdict(lambda : [Decimal(0), Decimal(0)])
        for x in self._actions:
            sub = x.flat_tax
            for year, value in sub.items():
                result[year][0] += value[0]
                result[year][1] += value[1]

        for action, value in self._taxCalculations:
            action.time.year
            if value >= Decimal(0):
                result[action.time.year][1] += value
            else:
                result[action.time.year][0] += value
        return result

    @property
    def flat_actions(self):
        actions = []
        stack = [ x for x in self._actions ]
        while stack:
            act = stack[0]
            actions.append(act)
            del stack[0]
            stack += [ x for x in act.actions ]
        return actions
    
    @property
    def actions(self):
        return self._actions

    @property
    def percent(self):
        return self._percent

    def addAction(self, action):
        action._parent = self
        self._actions.add(action)

    def addTaxCalculation(self, action, value):
        self._taxCalculations.append((action, value))
    
    def dump(self, prefix = ''):
        p = '' if not self._percent else "(%s %%)" % (str(self._percent))
        print('%s %s %s %s %s %s' % (prefix, self._time, self._actionType.name, self._count, self._asset, p))
        for x in self._actions:
            x.dump(prefix+'\t')
