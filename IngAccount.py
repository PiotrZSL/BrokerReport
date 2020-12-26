from Account import Account
from ImportUtils import getCsv, cleanText, fixNumber
from Action import Action, EActionType
from decimal import Decimal
from datetime import datetime
import os

class IngAccount(Account):
    def __init__(self, name, folder):
        super().__init__(name, "ING Bank Śląski")
        self._import(folder)

    def _import(self, folder):

        # import finance to get transationId to ISIN mapping
        isin_mapping = {}
        for name in os.listdir(folder):
            if not name.startswith('historiaFinansowa_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name))
            prev_dividend = None

            for row in csv:
                time = datetime.fromisoformat("-".join(reversed(row['Data operacji'].split('-'))))

                if row['Typ operacji'] == cleanText('Dywidendy') and row['Opis'].startswith(cleanText('DVCA Dywidenda pieniężna')):
                    isin = row['Opis'].split(':', 1)[0].split(' ')[-1].strip()
                    count =  Decimal(row['Opis'].split(':', 1)[1].split(' x ', 1)[0])
                    income = Decimal(fixNumber(row['Kwota']))
                    if 'rozliczenie' in row['Opis']:
                        main = Action(time,
                                      EActionType.DIVIDEND,
                                      count,
                                      self.stock(isin=isin, exchange='WWA', currency='PLN'))

                        sub = Action(time,
                                     EActionType.INCOME,
                                     income,
                                     self.currency(row['Waluta']))

                        main.addAction(sub)
                        self._add(main)
                        prev_dividend = sub
                        continue

                    if 'podatek' in row['Opis'] and prev_dividend:
                        sub = Action(time,
                                     EActionType.TAX,
                                     income,
                                     self.currency(row['Waluta']))
                        prev_dividend.addAction(sub)
                        prev_dividend = None
                        continue

                if row['Typ operacji'] == '' and (row['Opis'] == cleanText('Saldo początkowe') or row['Opis'] == cleanText('Saldo końcowe')):
                    continue

                if row['Typ operacji'] == cleanText('Wpłaty/wypłaty'):
                    value = Decimal(fixNumber(row['Kwota']))
                    cur = row['Waluta']

                    self._add(Action(time,
                                     EActionType.RECEIVE if value > Decimal(0) else EActionType.SEND,
                                     value,
                                     self.currency(cur)))
                    continue

                if row['Typ operacji'] == cleanText('Blokady pod zlecenia') or row['Typ operacji'] == cleanText('Transakcje'):
                    data = row['Opis'].split(',', 2)
                    isin = data[-2].strip()
                    transation = data[-3].split(' ')[-1].strip()
                    isin_mapping[transation] = isin
                    continue

        for name in os.listdir(folder):
            if not name.startswith('historiaTransakcji_') or not name.endswith('.csv'):
                continue

            csv = getCsv(os.path.join(folder, name))
            for row in csv:
                d = [int(x) for x in row['Data transakcji'].replace('-', ' ').split(' ')]
                time = datetime(d[2], d[1], d[0], d[3], d[4], d[5])
                nr = row['Numer zlecenia']
                isin = isin_mapping[nr]
                k = row['Kierunek'] == 'Kupno'
                main = Action(time,
                              EActionType.BUY if k else EActionType.SELL,
                              Decimal(fixNumber(row[cleanText('Ilość')])) * (Decimal(1) if k else Decimal(-1)),
                              self.stock(isin=isin, ticker=row['Papier'], exchange='WWA', currency='PLN'))

                cost = Action(time,
                              EActionType.PAYMENT if k else EActionType.INCOME,
                              Decimal(fixNumber(row[cleanText('Wartość')])) * (Decimal(-1) if k else Decimal(1)),
                              self.currency('PLN'))
                main.addAction(cost)

                fee = Action(time,
                             EActionType.FEE,
                             Decimal(fixNumber(row[cleanText('Prowizja')]))*Decimal(-1),
                             self.currency('PLN'))
                
                main.addAction(fee)
                self._add(main)
