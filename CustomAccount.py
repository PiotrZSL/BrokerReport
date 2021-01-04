from Account import Account
from ImportUtils import getExcel
from Action import Action, EActionType
from decimal import Decimal
from datetime import datetime
import os
import xlrd

class CustomAccount(Account):
    def __init__(self, name, folder):
        super().__init__(name, "Custom")
        self._import(folder)

    def _import(self, folder):
        self.__import(folder)
    
    def __import(self, folder):
        for name in os.listdir(folder):
            if not name.endswith('.xlsx'):
                continue

            def getValue(x):
                try:
                    return Decimal(str(x))
                except:
                    return Decimal(0)

            excel = getExcel(os.path.join(folder, name))
            xls = excel.sheet_by_index(0)

            for idx in range(1, xls.nrows):
                row = xls.row(idx)
                d = datetime(*xlrd.xldate_as_tuple(row[0].value, excel.datemode))
                asset = self.currency(row[1].value)
                price_currency = self.currency(row[5].value) if row[5].value else None
                if not asset and price_currency:
                    name = row[1].value.split(':', 1)[1] if ':' in row[1].value else row[1].value
                    ext = row[1].value.split(':', 1)[0] if ':' in row[1].value else None
                    asset = self.stock(ticker=name, exchange=ext, currency=row[5].value)

                if not asset:
                    raise Exception("Unknown asset: %s" % (row[1].value))

                count = getValue(row[3].value)
                price = getValue(row[4].value)
                fee = getValue(row[6].value)
                fee_currency = self.currency(row[7].value) if row[7].value else None
                
                if row[2].value == "Transfer":
                    main = Action(d,
                                  EActionType.RECEIVE if count > Decimal(0) else EActionType.SEND,
                                  count,
                                  asset)
                    if not fee.is_zero() and fee_currency:
                        main.addAction(Action(d,
                                              EActionType.FEE,
                                              fee,
                                              fee_currency))
                    self._add(main)
                    continue

                if row[2].value == "Buy" or row[2].value == "Sell":
                    main = Action(d,
                                  EActionType.BUY if row[2].value == "Buy" else EActionType.SELL,
                                  count,
                                  asset)
                    sub = Action(d,
                                 EActionType.PAYMENT if row[2].value == "Buy" else EActionType.INCOME,
                                 price * (Decimal(-1) if row[2].value == "Buy" else Decimal(1)),
                                 price_currency)
                    main.addAction(sub)

                    if not fee.is_zero() and fee_currency:
                        main.addAction(Action(d,
                                              EActionType.FEE,
                                              fee,
                                              fee_currency))

                    self._add(main)
                    continue
                
                raise Exception('Not supported row: %s' % (str(row[2])))
