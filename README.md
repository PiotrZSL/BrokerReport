# Broker Report

Cel tego projektu to stworzyć skrypt który by importował raporty inwestycyjne z Exante, Dif Broker, mBank, ING i wyliczał zyski i straty potrzebne do rozliczenia z fiskusem w Polsce. Skrypt jest eksperymentalny, i wszelkie dane które wypluje powinny być sprawdzone przez "niezależnych ekspertów". Autor nie bierze odpowiedzialności za nic. Używasz na własne ryzysko.

## Import Danych
Skrypt na wejście bierze folder który ma strukturę:

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
- ING pobiera niekiedy mniejszy podatek niż 19% (np. 18.7%)- do sprawdzenia jak przyjdzie PIT-8C czy to efekt zaokrąglania (i tak ma być) czy może PIT wykaże konieczną dopłatę z tego tytułu.

### mBank (mDM)
