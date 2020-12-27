# Broker Report

Cel tego projektu to stworzyć skrypt który by importował raporty inwestycyjne z Exante, Dif Broker, mBank, ING i wyliczał zyski i straty potrzebne do rozliczenia z fiskusem w Polsce. Skrypt jest eksperymentalny, i wszelkie dane które wypluje powinny być sprawdzone przez "niezależnych ekspertów". Autor nie bierze odpowiedzialności za nic. Używasz na własne ryzysko.

## Uruchomienie

Przykład uruchomienia:
```
python3 Main.py  --reports-folder /nas/Makler/ --output-xls file.xlsx --cache-file cache.pickle
```

Help:
```
usage: Main.py [-h] [--cache-file CACHE_FILE] --reports-folder REPORTS_FOLDER --output-xls OUTPUT_XLS

Makler Reports Processor

optional arguments:
  -h, --help            show this help message and exit
  --cache-file CACHE_FILE
                        location of optional cache file used to reduce network usage
  --reports-folder REPORTS_FOLDER
                        location of folder with reports to import, folder should contain `broker/account_name` folders with required reports in it
  --output-xls OUTPUT_XLS
                        output location of cumulative excel report to generate
```

Skrypty mogą wymagac doinstalowania brakujących pakietów przez `pip3`.

## Import Danych
Skrypt na wejście bierze folder który ma strukturę:

```
Input Directory
 - DIF
   - ACCOUNT1
   - ACCOUNT2
   - ...
 - EXANTE
   - ACCOUNT3
   - ACCOUNT4
   - ...
 - ING
   - ACCOUNT5
   - ACCOUNT6
   - ...
 - MBANK
   - ACCOUNT7
   - ACCOUNT8
   - ...
```

Nazwy kont mogą być dowolne.

### ING Bank Śląski

ING jako polski bank wysyła PIT-8C, przez co wszelkie dane liczone przez skrypt są głownie poglądowe. Drugie uproszczenie to że ING udostępnia tylko instrumenty z GPW.
Każde konto z ING powinno zawierać 2 typy plików z tego samego okresu: 
 - historiaFinansowa_*.csv
 - historiaTransakcji_*.csv
Samych plików może być więcej (np. raporty z każdego miesiąca z osobna), lecz zaleca się jeden wspólny raport jeśli to możliwe.

Historia Finansowa jest używana do wyciągania danych o dywidendach, wpłatach, wypłatach i ISNI walorów.
Historia Transakcji jest używana tylko do importu transakcji.

Uwagi:
- Testowano import tylko danych z GPW
- Wciąż może posiadać błędy
- ING pobiera niekiedy mniejszy podatek niż 19% (np. 18.7%)- do sprawdzenia jak przyjdzie PIT-8C czy to efekt zaokrąglania (i tak ma być) czy może PIT wykaże konieczną dopłatę z tego tytułu.

### mBank (mDM)

mBank jako polski bank wysyła PIT-8C, przez co wszelkie dane liczone przez skrypt są głownie poglądowe.
Każde konto z mBank powinno zawierać 2 typy plików z tego samego okresu:
 - Historia operacji finansowych *.csv (wraz z transakcjami)
 - Historia transakcji *.csv

Samych plików może być więcej (np. raporty z każdego miesiąca z osobna), lecz zaleca się jeden wspólny raport jeśli to możliwe.

Historia operacji finansowych jest używana do wyciągania danych o dywidendach, wpłatach, wypłatach, kosztach wypłat i mapowaniu ISNI.
Historia transakcji jest używana tylko do importu transakcji.

Uwagi:
- Testowano tylko import danych z GPW i zagranicznych giełd
- Testowano tylko konwersje walut z USD
- Wciąż może posiadać błędy
- Brak dokładnych danych o podatku od dywidend
- Testy diwidend wykonane tylko na rachunku IKZE - przez co na zwykłym rachunku może coś nie grać (podatek)

### Dif Broker

Dif Broker posiada najgorsze do obróbki raporty, a to że jest to zagraniczny broker nie ułatwia zbyt wiele.
Każde konto z Dif Broker powinno zawierac 3 typy plików z tego samego okresu:
 - TradesExecuted_*.xlsx
 - CashTransactions*.xlsx
 - ShareDividends_*.xlsx
Samych plików może być więcej (np. raporty z każdego miesiąca z osobna), lecz zaleca się jeden wspólny raport jeśli to możliwe.

Trades Executed jest używany do importu transakcji i forex (druga zakładka)
Cash Transactions jest używany do import custody fee, wpłat i przewalutowania wpłat
Share Dividends jest używany do importu dywidend

Uwagi:
 - Nie testowano kupna CFD, Opcji, Kontraktów, Obligacji, Wypłat
 - Wciąż może posiadać błędy
 - Import transakcji Forex jest mocno uproszczony
 - Nie importuje opłat za abonamenty
 - Nie testowano dywidend w innej walucie niż waluta rachunku
 - Nie testowano transakcji w innej walucie niż waluta rachunku

### Exante

Exante, zagraniczny broker posiada bardzo fajne raporty. Najlepiej jest wygenerować osobne raporty "custom" w języku angielskim.
Każde konto z Exante powinno zawierac 2 pliki:
 - Trades_*.csv (eksport: Handel/Trades)
 - Financial_*.csv (eksport: Transakcje finansowe/Financial Transactions)
Samych plików może być więcej (np. raporty z każdego miesiąca z osobna), lecz zaleca się jeden wspólny raport jeśli to możliwe.

Pliki te są zestawiane razem (walidacja czy wszystko się zgadza) i importowane.

Uwagi:
 - Nie testowano kupna CFD, Opcji, Kontraktów, Obligacji, Wypłat, Crypto
 - Transakacje gotówkowe i auto-konwersji są wyświelane tak samo
 - Nie testowano dywidend w innej walucie niż waluta rachunku
 - Nie testowano jeszcze transakcji forex

## Liczenie podatku
Ogólnie w przypadku mBank/ING jest to trochę zbędne, bo tam mamy PIT-8C. W przypadku Exante/Dif podatek jest liczony eksperymentalnie.

Uwagi:
 - Shortowanie nie jest zaimplementowane
 - % dywidendy nie zawsze się może zgadzać (testowano tylko dywidendy z 15% podatku u źródła)
 - Dywidendy od polskich akcji technicznie powinny być rozliczane w innym polu na formularzu PIT-38.
 - Custody Fee liczone jako koszt
 - Zastosowano metode FIFO, nawet dla Dif który niby ma zarządzanie na poziomie pozycji

## TODO
 - Shortowanie
 - Dokładniejsze rozbicie transakcji forex
 - Testy, testy, testy
 - Liczenie podatku w oparciu o pozycje dla Dif a nie FIFO
 - Dodanie kolejnej tabelki z aktualnym stanem konta (w celu weryfikacji)
 - Dodanie zakładki "Summary" z listą danych i info w które pola w PIT-38 powinny byc wpisane
 - Dodanie pełnych nazw akcji
 - Dodanie wspracia dla abonamentów w Dif i innych brakujących pozycji
 - Dodanie widoku transakcji z info ile straciliśmy/zarobiliśmy na pozycji
 - Dodanie aktualną wycenę walorów
 - Dodanie wsparcie dla "custom" brokera - tak gybyśmy chcieli wpisywac sobie np. zakupy metali szlachetnych
 - ...


