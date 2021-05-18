import unittest
import TaxUtils
from decimal import Decimal

class TaxUtilsTests(unittest.TestCase):

    def test_nbp_pln(self):
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(1), "PLN", "2020-12-02"), Decimal(1))
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(2), "PLN", "2020-12-02"), Decimal(2))

    def test_nbp_usd(self):
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(1), "USD", "2020-12-02"), Decimal("3.7367"))
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(2), "USD", "2020-12-02"), Decimal(2)*Decimal("3.7367"))
    
    def test_nbp_eur(self):
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(1), "EUR", "2020-12-02"), Decimal("4.4769"))
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(2), "EUR", "2020-12-02"), Decimal(2)*Decimal("4.4769"))
    
    def test_nbp_usd_after_weekend(self):
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(1), "USD", "2020-12-07"), Decimal("3.6765"))
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(2), "USD", "2020-12-07"), Decimal(2)*Decimal("3.6765"))
    
    def test_nbp_eur_after_weekend(self):
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(1), "EUR", "2020-12-07"), Decimal("4.4732"))
        self.assertEqual(TaxUtils.getNBPValueDayBefore(Decimal(2), "EUR", "2020-12-07"), Decimal(2)*Decimal("4.4732"))
        

