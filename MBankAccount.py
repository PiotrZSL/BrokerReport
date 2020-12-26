from Account import Account
from ImportUtils import getCsv, cleanText, checksum, fixNumber
from Action import Action, EActionType
from decimal import Decimal
from datetime import datetime
import os

class MBankAccount(Account):
    def __init__(self, name, folder):
        super().__init__(name, "mBank Biuro Maklerskie")
        self._import(folder)

    def _import(self, folder):

        # import finance to get transationId to ISIN mapping
        orders = []
        for name in os.listdir(folder):
            if not name.startswith('Historia operacji finansowych ') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name))

            last_send_outside = None
            for row in reversed(csv):
                time = datetime.fromisoformat("-".join(reversed(row[cleanText('Data księgowania')].split(' ', 1)[0].split('.'))))
                before =  Decimal(fixNumber(row[cleanText('Saldo początkowe')]))
                after = Decimal(fixNumber(row[cleanText('Saldo końcowe')]))
                kwota = after - before

                if row['Typ operacji'] == cleanText('Uznania') and row['Opis'].startswith('Dywidenda: '):
                    isin = row['Opis'].split('(', 1)[0].strip().split(' ')[-1]
                    name = row['Opis'].split('(', 1)[1].split(')', 1)[0].strip()
                    main = Action(checksum(row['Opis']),
                                  time,
                                  EActionType.DIVIDEND,
                                  Decimal(1),
                                  self.stock(isin=isin, ticker=name, currency='PLN'))

                    self._add(main)
                    main.addAction(Action(checksum(row['Opis']+'-cash'),
                                          time,
                                          EActionType.INCOME,
                                          kwota,
                                          self.currency('PLN')))
                    continue

                if row['Typ operacji'] == cleanText('Uznania') and 'Dywid.' in row['Opis'] and len(row['Opis'].split(';')) == 3:
                    #K039 Dywid. 261 szt PJSC GAZPR US3682872078; brutto 0.413 USD/szt; USD/PLN 3.6752
                    isin = row['Opis'].split(';')[0].split(' ')[-1]
                    szt = Decimal(row['Opis'].split('szt ', 1)[0].strip().split(' ')[-1])
                    value = Decimal(row['Opis'].split('brutto ', 1)[1].split(' ')[0])
                    cur = row['Opis'].split('/szt', 1)[0].split(' ')[-1]
                    conv = Decimal(row['Opis'].split('/PLN ', 1)[1].strip())

                    main = Action(checksum(row['Opis']),
                                  time,
                                  EActionType.DIVIDEND,
                                  szt,
                                  self.stock(isin=isin, currency=cur))
                    self._add(main)
                    
                    sub = Action(checksum(row['Opis']+"-gain"),
                                 time,
                                 EActionType.INCOME,
                                 value*szt,
                                 self.currency(cur))

                    main.addAction(sub)

                    sub2 = Action(checksum(row['Opis']+"-convert"),
                                  time,
                                  EActionType.SELL,
                                  kwota/conv*Decimal(-1),
                                  self.currency(cur))

                    sub.addAction(sub2)

                    sub2.addAction(Action(checksum(row['Opis']+"-pln"),
                                   time,
                                   EActionType.BUY,
                                   kwota,
                                   self.currency('PLN')))

                    sub.addAction(Action(checksum(row['Opis']+"-tax"),
                                          time,
                                          EActionType.TAX,
                                          kwota/conv-szt*value,
                                          self.currency(cur)))
                    continue
            
                if row['Typ operacji'] == cleanText('Obciążenia') and row['Opis'].startswith('Przelew na rachunek bankowy'):
                    # sending funds
                    main = Action(checksum(row['Opis']),
                                  time,
                                  EActionType.SEND,
                                  kwota,
                                  self.currency(row['Opis'].split('/')[-1].strip()))
                    last_send_outside = main
                    self._add(main)
                    continue

                if row['Typ operacji'] == cleanText('Obciążenia') and row['Opis'].startswith(cleanText('Księgowanie prowizji od dyspozycji przelewu')) and last_send_outside:
                    # sending funds - fee
                    main = Action(checksum(row['Opis']),
                                  time,
                                  EActionType.FEE,
                                  kwota,
                                  last_send_outside.asset)
                    last_send_outside.addAction(main)
                    last_send_outside = None
                    continue

                last_send_outside = None
                
                if row['Typ operacji'] == cleanText('Uznania') and row['Opis'].startswith('WYC.BK:'):
                    # new funds adding
                    main = Action(checksum(row['Opis']),
                                  time,
                                  EActionType.RECEIVE,
                                  kwota,
                                  self.currency('PLN'))
                    self._add(main)
                    continue

                if row['Typ operacji'] == cleanText('Uznania') and row['Opis'].startswith('NOT:'):
                    # - money
                    orders.append((time, kwota, row['Opis'].split('PW:', 1)[1].strip()))
                    continue
                
                if row['Typ operacji'] == cleanText('Obciążenia') and row['Opis'].startswith('NOT:'):
                    # + money
                    orders.append((time, kwota, row['Opis'].split('PW:', 1)[1].strip()))
                    continue

                raise Exception('Unsupported record: %s' % (row))

        orders.sort(key=lambda x : x[0])

        transations = []
        for name in os.listdir(folder):
            if not name.startswith('Historia transakcji ') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name))
            for row in csv:
                d = [int(x) for x in row['Czas transakcji'].replace(':', ' ').replace('.', ' ').split(' ')]
                time = datetime(d[2], d[1], d[0], d[3], d[4], d[5])
                transations.append((time, row))

        transations.sort(key=lambda x : x[0])
        for time, row in transations:
            currency = row['Waluta rozliczenia']
            count = Decimal(fixNumber(row['Liczba']))
            value = Decimal(fixNumber(row['Kurs']))
            stokcCurrency = row['Waluta']
            sumValue = Decimal(fixNumber(row[cleanText('Wartość')]))
            fee = Decimal(fixNumber(row['Prowizja']))
        
            crc = str(row)
            k = row['K/S'] == 'K'

            order = orders.pop(0)
            if order[0].date() != time.date() or sumValue * (Decimal(-1) if k else Decimal(1)) != order[1]:
                raise Exception("Finance and Transation history don't match: %s != %s" % (str(order), str(row)))

            if fee:
                feeOrder = orders.pop(0)
                if feeOrder[0].date() != time.date() or -fee != feeOrder[1] or feeOrder[2] != order[2]:
                    raise Exception("Finance and Transation history don't match: %s != %s" % (str(feeOrder), str(row)))

            main = Action(checksum(crc),
                          time,
                          EActionType.BUY if k else EActionType.SELL,
                          count * (Decimal(1) if k else Decimal(-1)),
                          self.stock(isin=order[2], ticker=row['Walor'], exchange=row[cleanText('Giełda')], currency=stokcCurrency))

            self._add(main)

            if fee:
                f = Action(checksum(crc),
                           time,
                           EActionType.FEE,
                           -fee,
                           self.currency(currency))
                main.addAction(f)

            if stokcCurrency != currency:
                sub = Action(checksum(crc),
                             time,
                             EActionType.SELL if k else EActionType.BUY,
                             value * count * (Decimal(-1) if k else Decimal(1)),
                             self.currency(stokcCurrency))

                main.addAction(sub)
                
                sub2 = Action(checksum(crc),
                              time,
                              EActionType.BUY if k else EActionType.SELL,
                              value * count * (Decimal(1) if k else Decimal(-1)),
                              self.currency(stokcCurrency))

                sub.addAction(sub2)
                main = sub2

            sub3 = Action(checksum(crc),
                          time,
                          EActionType.SELL if k else EActionType.BUY,
                          sumValue * (Decimal(-1) if k else Decimal(1)),
                          self.currency(currency))

            main.addAction(sub3)

        if orders:
            raise Exception('Not all orders consumed: %s' % (str(orders)))
