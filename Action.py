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
    TAX_PENDING = 11

class Action:
    def __init__(self, actionId, time, actionType, count, asset):
        self._actionId = actionId
        self._time = time
        self._actionType = actionType
        self._count = count
        self._asset = asset
        self._parent = None
        self._actions = SortedList(key=lambda x : x.time)

    @property
    def id(self):
        return self._actionId

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
    def actions(self):
        return self._actions

    def addAction(self, action):
        action._parent = self
        self._actions.add(action)
    
    def dump(self, prefix = ''):
        print('%s%s - %s %s %s %s' % (prefix, self._actionId, self._time, self._actionType.name, self._count, self._asset))
        for x in self._actions:
            x.dump(prefix+'\t')


class TaxAction(Action):
    def __init__(self, actionId, year, time, actionType, count, asset):
        super().__init__(actionId, time, time, count, asset)
        self._year = year

    @property
    def year(self):
        return self._year
