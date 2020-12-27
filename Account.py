from sortedcontainers import SortedList
from Asset import *

class Account:
    def __init__(self, name, broker):
        self._name = name
        self._broker = broker
        self._assets = AssetDatabase()
        self._actions = SortedList(key=lambda x : x.time)

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
