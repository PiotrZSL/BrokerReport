from enum import Enum
from sortedcontainers import SortedList

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
