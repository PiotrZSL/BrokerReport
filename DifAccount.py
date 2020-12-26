from Account import Account
from ImportUtils import getExcel, cleanText, checksum, fixNumber
from Action import Action, EActionType
from decimal import Decimal
from datetime import datetime
import os
import xlrd

class DifAccount(Account):
    def __init__(self, name, folder):
        super().__init__(name, "DIF Broker")
        self._import(folder)

    def _import(self, folder):
        self.__importCash(folder)
        self.__importDividents(folder)
        self.__importTransations(folder)
    
    def __importCash(self, folder):
        for name in os.listdir(folder):
            if not name.startswith('CashTransactions') or not name.endswith('.xlsx'):
                continue

            excel = getExcel(os.path.join(folder, name))
            xls = excel.sheet_by_index(0)
    
            for idx in range(1, xls.nrows):
                row = xls.row(idx)
                d = datetime(*xlrd.xldate_as_tuple(row[8].value, excel.datemode))
                inputValue = Decimal(fixNumber(row[4].value.replace(',', '.').split(' ', 1)[0]))
                inputCurency = row[4].value.split(' ', 1)[1]
                outputValue = Decimal(fixNumber(row[5].value.replace(',', '.').split(' ', 1)[0]))
                outputCurency = row[5].value.split(' ', 1)[1]

                if row[2].value == 'Depozyt zabezpieczający':
                    main = Action(checksum(str(row[1].value)),
                                  d,
                                  EActionType.RECEIVE,
                                  inputValue,
                                  self.currency(inputCurency))

                    self._add(main)
                    
                    if outputCurency != inputCurency:
                        sub = Action(checksum(str(row[1].value)+"-convert"),
                                     d,
                                     EActionType.SELL,
                                     inputValue*Decimal(-1),
                                     self.currency(inputCurency))

                        main.addAction(sub);

                        sub.addAction(Action(checksum(str(row[1].value)+"-base"),
                                            d,
                                            EActionType.BUY,
                                            outputValue,
                                            self.currency(outputCurency)))
                    continue

                if cleanText(row[2].value) == cleanText('Wycofanie środków'):
                    
                    main = Action(checksum(str(row[1].value)),
                                  d,
                                  EActionType.SEND if row[3].value != "Custody Fee" else EActionType.FEE,
                                  inputValue,
                                  self.currency(inputCurency))
                    self._add(main)

    def __importDividents(self, folder):
        for name in os.listdir(folder):
            if not name.startswith('ShareDividends_') or not name.endswith('.xlsx'):
                continue
            excel = getExcel(os.path.join(folder, name))
            xls = excel.sheet_by_index(0)

            for idx in range(1, xls.nrows):
                row = xls.row(idx)
                if row[4].value != 'Cash Dividend':
                    raise Exception('Record not supported: %s' % (str(row)))

                d = datetime(*xlrd.xldate_as_tuple(row[6].value, excel.datemode))
                fiat = row[9].value.split(' ', 1)[0]
                value = Decimal(fixNumber(row[9].value.replace(fiat, '')))

                if fiat not in row[11].value:
                    raise Exception('Dividend with difrent tax currency not supported: %s' % (str(row)))

                tax = Decimal(fixNumber(row[11].value.replace(fiat, '')))
                percent = Decimal(fixNumber(row[10].value))

                afiat = row[2].value
                main = Action(checksum(str(row)),
                              d,
                              EActionType.DIVIDEND,
                              Decimal(fixNumber(row[7].value)),
                              self.stock(name=row[3].value, currency=fiat))

                self._add(main)

                main2 = Action(checksum(str(row)),
                               d,
                               EActionType.INCOME,
                               value,
                               self.currency(fiat))

                main.addAction(main2)
                
                if afiat != fiat:
                    s = Action(checksum(str(row)+'-sell'),
                               d,
                               EActionType.SELL,
                               value*Decimal(-1),
                               self.currency(fiat))
                    main2.addAction(s)

                    s.addAction(Action(checksum(str(row)+'-buy'),
                                d,
                                EActionType.BUY,
                                Decimal(fixNumber(row[16].value)),
                                self.currency(afiat)))

                if not tax.is_zero():
                    main2.addAction(Action(checksum(str(row)+'-tax'),
                                          d,
                                          EActionType.TAX,
                                          tax,
                                          self.currency(fiat),
                                          percent))

    def __importTransations(self, folder):
        for name in os.listdir(folder):
            if not name.startswith('TradesExecuted_') or not name.endswith('.xlsx'):
                continue

            excel = getExcel(os.path.join(folder, name))
            xls = excel.sheet_by_index(1)

            for idx in range(1, xls.nrows):
                row = xls.row(idx)
                tId = str(row[0].value)
                name = row[2].value.split('(', 1)[0].strip()
                isin = None if 'ISIN:' not in row[2].value else row[2].value.split('ISIN:', 1)[1].split(')')[0].strip()
                ticker = row[11].value.split(':', 1)[0] if ':' in row[11].value else row[11].value
                ex = row[11].value.split(':', 1)[1] if ':' in row[11].value else None

                d = datetime(*xlrd.xldate_as_tuple(row[3].value, excel.datemode))

                count = Decimal(fixNumber(row[6].value))
                value = Decimal(fixNumber(row[8].value))

                blockedAcount = Decimal(fixNumber(row[20].value))
                blockedClient = Decimal(fixNumber(row[19].value))

                accountCurrency = row[18].value
                clientCurrency = row[21].value
                
                k = row[4].value == 'Bought'

                if accountCurrency != clientCurrency:
                    raise Exception('Transations bettwen %s - %s were not tested & implemented' % (accountCurrency, clientCurrency))

                if row[16].value == 'FxSpot':

                    main = Action(checksum(tId),
                                  d,
                                  EActionType.FOREX,
                                  count,
                                  self.stock(None, ticker, ex, clientCurrency, name))

                    if not value.is_zero():
                        main.addAction(Action(checksum(tId),
                                       d,
                                       EActionType.PAYMENT if k else EActionType.INCOME,
                                       blockedClient,
                                       self.currency(clientCurrency)))
                    self._add(main)
                    continue

                main = Action(checksum(tId),
                              d,
                              EActionType.BUY if k else EActionType.SELL,
                              count,
                              self.stock(isin, ticker, ex, clientCurrency, name))

                self._add(main)

                sub = Action(checksum(tId+"mn"),
                             d,
                             EActionType.SELL if k else EActionType.BUY,
                             value,
                             self.currency(clientCurrency))
                main.addAction(sub)

                cost = blockedClient - value

                if cost:
                    sub2 = Action(checksum(tId+"cost"),
                                  d,
                                  EActionType.FEE,
                                  cost,
                                  self.currency(clientCurrency))
                    main.addAction(sub2)
