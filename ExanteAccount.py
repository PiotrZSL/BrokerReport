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
                if fee:
                    main.addAction(Action(checksum(row['Order Id']),
                                          time,
                                          EActionType.FEE,
                                          fee*Decimal(-1),
                                          self.currency(row['Commission Currency'])))
                    transations.append((time, row['Symbol ID'], 'COMMISSION', fee*Decimal(-1), row['Commission Currency']))
                
                transations.append((time, row['Symbol ID'], 'TRADE', sub.count, sub.asset.ticker))
                transations.append((time, row['Symbol ID'], 'TRADE', main.count, main.asset.ticker))

        transations.sort(key=lambda x: x[0])

        financial = []

        for name in os.listdir(folder):
            if not name.startswith('Financial_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name), '\t', 'utf-16')

            for row in reversed(csv):
                d = [int(x) for x in row['Time'].replace('-', ' ').replace(':', ' ').split(' ')]
                time = datetime(d[0], d[1], d[2], d[3], d[4], d[5])
                
                financial.append((time, row))

        financial.sort(key=lambda x: x[0])
        print(financial)


