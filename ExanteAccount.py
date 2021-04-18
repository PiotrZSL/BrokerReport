from Account import Account
from ImportUtils import getCsv, cleanText, fixNumber
from Action import Action, EActionType
from Exchanges import Exchange
from decimal import Decimal
from datetime import datetime
import os
import xlrd

class ExanteAccount(Account):
    def __init__(self, name, folder):
        super().__init__(name, "Exante")
        self._ex = Exchange("Cyprus", "CY", "EXANTE") 
        self._import(folder)
        self._finishImport()

    def _import(self, folder):

        transations = []

        C_TIME = 0
        C_COUNT = 8
        C_ISIN = 4
        C_SYMBOL = 3
        C_CURRENCY = 7
        C_TYPE = 5
        C_VOLUME = 12
        C_GAIN = 11
        C_SIDE = 2
        C_COMMISSION = 9
        C_COMMISSION_CURRENCY = 10

        for name in os.listdir(folder):
            if not name.startswith('Trades_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name), '\t', 'utf-16')
            if not csv:
                continue


            for row in reversed(csv):
                d = [int(x) for x in row[C_TIME].replace('-', ' ').replace(':', ' ').split(' ')]
                time = datetime(d[0], d[1], d[2], d[3], d[4], d[5])

                k = row[C_SIDE] == 'buy'

                e = None if '.' not in row[C_SYMBOL] else row[C_SYMBOL].split('.', 1)[1]
                if row[C_SYMBOL].endswith('.E.FX'):
                    e = self._ex
                main = Action(time,
                              EActionType.BUY if k else EActionType.SELL,
                              Decimal(fixNumber(row[C_COUNT]))*(Decimal(1) if k else Decimal(-1)),
                              self.stock(None if row[C_ISIN] == 'None' else row[C_ISIN],
                                         row[C_SYMBOL].split('.', 1)[0],
                                         e,
                                         row[C_CURRENCY]) if row[C_TYPE] != 'FOREX' else self.currency(row[C_SYMBOL].split('/')[0]))
                self._add(main)

                v = Decimal(fixNumber(row[C_VOLUME]))*(Decimal(-1) if k else Decimal(1)) if not row[C_SYMBOL].endswith('.E.FX') else Decimal(fixNumber(row[C_GAIN]))
                if not v.is_zero():
                    sub = Action(time,
                                 EActionType.PAYMENT if v < Decimal(0) else EActionType.INCOME,
                                 v,
                                 self.currency(row[C_CURRENCY]))

                    main.addAction(sub)

                fee = Decimal(fixNumber(row[C_COMMISSION]))
                transation = []
                if fee:
                    main.addAction(Action(time,
                                          EActionType.FEE,
                                          fee*Decimal(-1),
                                          self.currency(row[C_COMMISSION_CURRENCY])))
                    transations.append((time, row[C_SYMBOL], 'COMMISSION', fee*Decimal(-1), row[C_COMMISSION_CURRENCY]))
                
                if not v.is_zero():
                    transations.append((time, row[C_SYMBOL], 'TRADE', v, row[C_CURRENCY]))
                transations.append((time, row[C_SYMBOL], 'TRADE', main.count, str(main.asset) if not row[C_SYMBOL].endswith('.E.FX') else row[C_SYMBOL]))

        financial = []

        F_WHEN = 5
        F_SYMBOL = 2
        F_TYPE = 4
        F_ASSET = 7
        F_COMMENT = 9
        F_SUM = 6

        for name in os.listdir(folder):
            if not name.startswith('Financial_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name), '\t', 'utf-16')
            if not csv:
                continue


            last = (None, None)
            for row in reversed(csv):
                d = [int(x) for x in row[F_WHEN].replace('-', ' ').replace(':', ' ').split(' ')]
                time = datetime(d[0], d[1], d[2], d[3], d[4], d[5])
                financial.append([time, row[F_SYMBOL], row])
        
        financial.sort(key=lambda x: x[0])

        def eraseTransation(time, symbol, row, transations):
            found = [ idx for idx, x in enumerate(transations) if time.date() == x[0].date() and symbol == x[1] and row[F_TYPE] == x[2] and Decimal(fixNumber(row[F_SUM])) == x[3] and row[F_ASSET] == x[4] ]
            if not found:
                return False

            del transations[found[0]]
            return True

        # process autoconversions first
        autoconversions = [ x for x in financial if x[2][F_TYPE] == 'AUTOCONVERSION' ]


        while autoconversions:
            time, symbol, row = autoconversions[0]
            del autoconversions[0]
            if autoconversions and autoconversions[0][2][F_SYMBOL] == row[F_SYMBOL] and autoconversions[0][2][F_WHEN] == row[F_WHEN]:
                row2 = autoconversions[0][2]
                del autoconversions[0]
                plus = row2 if Decimal(fixNumber(row2[F_SUM])) > Decimal(fixNumber(row[F_SUM])) else row
                minus = row2 if Decimal(fixNumber(row2[F_SUM])) < Decimal(fixNumber(row[F_SUM])) else row

                main = Action(time,
                              EActionType.PAYMENT,
                              Decimal(fixNumber(minus[F_SUM])),
                              self.currency(minus[F_ASSET]))

                sub = Action(time,
                             EActionType.BUY,
                             Decimal(fixNumber(plus[F_SUM])),
                             self.currency(plus[F_ASSET]))
                sub.addAction(main)
                self._add(sub)
                continue

            raise Exception("Not suported row: %s" % (str(row)))

        financial = [x for x in financial if x[2][F_TYPE] != 'AUTOCONVERSION' ]

        while financial:
            time, symbol, row = financial[0]
            if row[F_TYPE] == 'TRADE' or row[F_TYPE] == 'COMMISSION':
                if not eraseTransation(time, symbol, row, transations):
                    print(transations)
                    raise Exception("Not consumed financial row: %s" % (str(row)))
                del financial[0]
                continue
            
            del financial[0]

            if row[F_TYPE] == 'FUNDING/WITHDRAWAL' or row[F_TYPE] == 'SUBACCOUNT TRANSFER':
                value = Decimal(fixNumber(row[F_SUM]))
                main = Action(time,
                              EActionType.RECEIVE if value > Decimal(0) else EActionType.SEND,
                              value,
                              self.currency(row[F_ASSET]))
                self._add(main)
                continue

            if row[F_TYPE] == 'TAX':
                    continue

            if row[F_TYPE] == 'DIVIDEND' and ' tax ' in row[F_COMMENT]:
                tax = Action(time,
                             EActionType.TAX,
                             Decimal(fixNumber(row[F_COMMENT].split(' tax ', 1)[1].split('(', 1)[0].strip())),
                             self.currency(row[F_ASSET]),
                             Decimal(fixNumber(row[F_COMMENT].split('(')[-1].split('%)', 1)[0])))

                main = Action(time,
                              EActionType.DIVIDEND,
                              Decimal(fixNumber(row[F_COMMENT].split('shares', 1)[0].strip())),
                              self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1], currency=row[F_ASSET]))

                income = Action(time,
                                EActionType.INCOME,
                                Decimal(fixNumber(row[F_SUM])),
                                self.currency(row[F_ASSET]))

                income.addAction(tax)
                main.addAction(income)
                self._add(main)
                continue

            if row[F_TYPE] == 'DIVIDEND':
                main = Action(time,
                              EActionType.DIVIDEND,
                              Decimal(fixNumber(row[F_COMMENT].split('shares', 1)[0].strip())),
                              self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1], currency=row[F_ASSET]))
                income = Action(time,
                                EActionType.INCOME,
                                Decimal(fixNumber(row[F_SUM])),
                                self.currency(row[F_ASSET]))
                main.addAction(income)
                self._add(main)
                continue

            if (row[F_TYPE] == 'EXERCISE' and
                financial and
                financial[0][2][F_TYPE] == row[F_TYPE] and
                financial[0][2][F_COMMENT] == row[F_COMMENT] and
                financial[0][2][F_SYMBOL] == row[F_SYMBOL] and
                row[F_COMMENT].endswith(' Exercised Rights')):
                    financial[0][2][F_TYPE] = 'TRADE'
                    row[F_TYPE] = 'TRADE'
                    financial = [(time, symbol, row)] + financial
                    continue

            if (row[F_TYPE] == 'CORPORATE ACTION' and 
                financial and
                financial[0][2][F_TYPE] == 'CORPORATE ACTION' and
                financial[0][2][F_WHEN] == row[F_WHEN] and
                financial[0][2][F_COMMENT] == row[F_COMMENT] and
                row[F_COMMENT] == "%s -> %s" % (financial[0][2][F_SYMBOL], symbol)):

                self._assets.changeName(financial[0][2][F_SYMBOL].split('.', 1)[0],
                                        financial[0][2][F_SYMBOL].split('.', 1)[1],
                                        symbol.split('.', 1)[0],
                                        symbol.split('.', 1)[1])
                del financial[0]
                continue
            
            if row[F_TYPE] == 'CORPORATE ACTION' and row[F_COMMENT].endswith(' Rights'):
                self._add(Action(time,
                                 EActionType.BUY,
                                 Decimal(fixNumber(row[F_SUM])),
                                 self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1])))
                continue
            
            if (row[F_TYPE] == 'STOCK SPLIT' and
                "Stock Split " in row[F_COMMENT] and
                len(financial) > 1 and
                financial[0][2][F_TYPE] == 'STOCK SPLIT' and
                financial[0][2][F_SYMBOL] == row[F_SYMBOL] and
                financial[1][2][F_TYPE] == 'STOCK SPLIT' and
                financial[1][2][F_SYMBOL] == row[F_SYMBOL]):

                row_cash = row if 'Fractional Share Payment' in row[F_COMMENT] else None
                if not row_cash:
                    row_cash = financial[0][2] if 'Fractional Share Payment' in financial[0][2][F_COMMENT] else financial[1][2]

                row_old = row if row[F_SYMBOL] == row[F_ASSET] and int(row[F_SUM]) < 0 else None
                if not row_old:
                    row_old = financial[0][2] if financial[0][2][F_ASSET] == row[F_SYMBOL] and int(financial[0][2][F_SUM])<0 else financial[1][2]

                row_new = row if row[F_SYMBOL] == row[F_ASSET] and int(row[F_SUM]) > 0 else None
                if not row_new:
                    row_new = financial[0][2] if financial[0][2][F_ASSET] == row[F_SYMBOL] and int(financial[0][2][F_SUM])>0 else financial[1][2]

                split = row_old[F_COMMENT].replace('Stock Split ','').split(" for ", 1)
                sold = Decimal(int(row_old[F_SUM]) + int(row_new[F_SUM]) * int(split[1]))
                split = Decimal(split[0]) / Decimal(split[1])
                asset = self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1], currency=row_cash[F_ASSET])

                def getTime(when):
                    d = [int(x) for x in row[F_WHEN].replace('-', ' ').replace(':', ' ').split(' ')]
                    return datetime(d[0], d[1], d[2], d[3], d[4], d[5])

                main = Action(getTime(row_old[F_WHEN]),
                              EActionType.SELL,
                              sold,
                              asset)
                income = Action(getTime(row_cash[F_WHEN]),
                                EActionType.INCOME,
                                Decimal(fixNumber(row_cash[F_SUM])),
                                self.currency(row_cash[F_ASSET]))

                main.addAction(income)
                self._add(main)
                self._split(asset, max(time, financial[0][0], financial[1][0]), split)
                del financial[0]
                del financial[0]
                continue
            
            if (row[F_TYPE] == 'STOCK SPLIT' and
                "Stock Split " in row[F_COMMENT] and
                financial and
                financial[0][2][F_TYPE] == 'STOCK SPLIT' and
                financial[0][2][F_COMMENT] == row[F_COMMENT] and
                financial[0][2][F_ASSET] == row[F_ASSET]):

                split = row[F_COMMENT].replace('Stock Split ','').split(" for ", 1)
                split = Decimal(split[0]) / Decimal(split[1])
                asset = self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1])

                self._split(asset, time, split)
                del financial[0]
                continue


            raise Exception("Not suported row: %s" % (str(row)))

        if transations:
            raise Exception("No all transations consumed: %s" % (str(transations)))

