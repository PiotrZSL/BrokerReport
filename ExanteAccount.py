from Account import Account
from ImportUtils import getCsv, cleanText, checksum, fixNumber
from Action import Action, EActionType
from decimal import Decimal
from datetime import datetime
import os
import xlrd

class ExanteAccount(Account):
    def __init__(self, name, folder):
        super().__init__(name, "Exante")
        self._import(folder)

    def _import(self, folder):

        transations = []

        for name in os.listdir(folder):
            if not name.startswith('Trades_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name), '\t', 'utf-16')

            for row in reversed(csv):
                d = [int(x) for x in row['Time'].replace('-', ' ').replace(':', ' ').split(' ')]
                time = datetime(d[0], d[1], d[2], d[3], d[4], d[5])

                k = row['Side'] == 'buy'

                main = Action(checksum(row['Order Id']),
                              time,
                              EActionType.BUY if k else EActionType.SELL,
                              Decimal(fixNumber(row['Quantity']))*(Decimal(1) if k else Decimal(-1)),
                              self.stock(None if row['ISIN'] == 'None' else row['ISIN'],
                                         row['Symbol ID'].split('.', 1)[0],
                                         None if '.' not in row['Symbol ID'] else row['Symbol ID'].split('.', 1)[1],
                                         row['Currency']) if row['Type'] != 'FOREX' else self.currency(row['Symbol ID'].split('/')[0]))
                self._add(main)

                sub = Action(checksum(row['Order Id']),
                             time,
                             EActionType.PAYMENT if k else EActionType.INCOME,
                             Decimal(fixNumber(row['Traded Volume']))*(Decimal(-1) if k else Decimal(1)),
                             self.currency(row['Currency']))

                main.addAction(sub)

                fee = Decimal(fixNumber(row['Commission']))
                transation = []
                if fee:
                    main.addAction(Action(checksum(row['Order Id']),
                                          time,
                                          EActionType.FEE,
                                          fee*Decimal(-1),
                                          self.currency(row['Commission Currency'])))
                    transation.append(('COMMISSION', fee*Decimal(-1), row['Commission Currency']))
                
                transation.append(('TRADE', sub.count, str(sub.asset)))
                transation.append(('TRADE', main.count, str(main.asset)))
                transations.append((time, row['Symbol ID'], transation))

        transations.sort(key=lambda x: x[0])

        financial = []

        for name in os.listdir(folder):
            if not name.startswith('Financial_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name), '\t', 'utf-16')

            last = (None, None)
            for row in reversed(csv):
                d = [int(x) for x in row['When'].replace('-', ' ').replace(':', ' ').split(' ')]
                time = datetime(d[0], d[1], d[2], d[3], d[4], d[5])
                financial.append([time, row['Symbol ID'], row])
        
        financial.sort(key=lambda x: x[0])

        while financial:
            time, symbol, row = financial[0]

            if transations and transations[0][0].date() == time.date() and symbol == transations[0][1] and len(financial)+1 >= len(transations[0][2]):
                rows = transations[0][2]
                found = True
                for idx, nrow in enumerate(rows):
                    if financial[idx][2]['Operation type'] != nrow[0] or Decimal(fixNumber(financial[idx][2]['Sum'])) != nrow[1] or  financial[idx][2]['Asset'] != nrow[2]:
                        found = False
                        break

                if not found:
                    raise Exception("Transation not found, files are not in sync - %s - %s" % (str(nrow), str(row)))

                del transations[0]
                for x in rows:
                    del financial[0]
                continue

            if row['Operation type'] == 'TRADE':
                raise Exception("Not consumed financial row: %s" % (str(row)))
            
            del financial[0]

            if row['Operation type'] == 'FUNDING/WITHDRAWAL' or row['Operation type'] == 'SUBACCOUNT TRANSFER':
                value = Decimal(fixNumber(row['Sum']))
                main = Action(checksum(row['Transaction ID']),
                              time,
                              EActionType.RECEIVE if value > Decimal(0) else EActionType.SEND,
                              value,
                              self.currency(row['Asset']))
                self._add(main)
                continue

            if (row['Operation type'] == 'AUTOCONVERSION' and 
                row['Symbol ID'] == 'None' and 
                financial and 
                financial[0][2]['Operation type'] == 'AUTOCONVERSION' and 
                financial[0][2]['Symbol ID'] == 'None' and
                financial[0][2]['When'] == row['When']):

                main = Action(checksum(row['Transaction ID']),
                              time,
                              EActionType.PAYMENT,
                              Decimal(fixNumber(row['Sum'])),
                              self.currency(row['Asset']))

                row = financial[0][2]
                del financial[0]
                sub = Action(checksum(row['Transaction ID']),
                             time,
                             EActionType.BUY,
                             Decimal(fixNumber(row['Sum'])),
                             self.currency(row['Asset']))
                sub.addAction(main)
                self._add(sub)
                continue

            if (row['Operation type'] == 'TAX' and
                financial and
                financial[0][2]['Operation type'] == 'DIVIDEND' and
                financial[0][2]['Symbol ID'] == symbol and
                financial[0][2]['When'] == row['When']):

                tax = Action(checksum(row['Transaction ID']),
                             time,
                             EActionType.TAX,
                             Decimal(fixNumber(row['Sum'])),
                             self.currency(row['Asset']))

                row = financial[0][2]
                del financial[0]

                main = Action(checksum(row['Transaction ID']),
                              time,
                              EActionType.DIVIDEND,
                              Decimal(fixNumber(row['Comment'].split('shares', 1)[0].strip())),
                              self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1], currency=row['Asset']))

                income = Action(checksum(row['Transaction ID']),
                                time,
                                EActionType.INCOME,
                                Decimal(fixNumber(row['Sum'])),
                                self.currency(row['Asset']))

                income.addAction(tax)
                main.addAction(income)
                self._add(main)
                continue

            if row['Operation type'] == 'DIVIDENT':
                main = Action(checksum(row['Transaction ID']),
                              time,
                              EActionType.DIVIDEND,
                              Decimal(fixNumber(row['Comment'].split('shares', 1)[0].strip())),
                              self.stock(ticker=symbol.split('.', 1)[0], exchange=symbol.split('.', 1)[1], currency=row['Asset']))
                self._add(main)
                continue

            if (row['Operation type'] == 'CORPORATE ACTION' and 
                financial and
                financial[0][2]['Operation type'] == 'CORPORATE ACTION' and
                financial[0][2]['When'] == row['When'] and
                financial[0][2]['Comment'] == row['Comment'] and
                row['Comment'] == "%s -> %s" % (financial[0][2]['Symbol ID'], symbol)):

                self._assets.changeName(financial[0][2]['Symbol ID'].split('.', 1)[0],
                                        financial[0][2]['Symbol ID'].split('.', 1)[1],
                                        symbol.split('.', 1)[0],
                                        symbol.split('.', 1)[1])
                del financial[0]
                continue

            raise Exception("Not suported row: %s" % (str(row)))

        if transations:
            raise Exception("No all transations consumed: %s" % (str(transations)))

