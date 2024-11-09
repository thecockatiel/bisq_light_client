import unittest 

from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.base.utils.monetary_format import MonetaryFormat

class TestFiat(unittest.TestCase): 
    def test_parse_and_value_of(self):
        self.assertEqual(Fiat.value_of("EUR", 10000), Fiat.parse_fiat("EUR", "1"))
        self.assertEqual(Fiat.value_of("EUR", 100), Fiat.parse_fiat("EUR", "0.01"))
        self.assertEqual(Fiat.value_of("EUR", 1), Fiat.parse_fiat("EUR", "0.0001"))
        self.assertEqual(Fiat.value_of("EUR", -10000), Fiat.parse_fiat("EUR", "-1"))

    def test_parse_fiat(self):
        self.assertEqual(1, Fiat.parse_fiat("EUR", "0.0001").value)
        self.assertEqual(1, Fiat.parse_fiat("EUR", "0.00010").value)

    def test_parse_fiat_overprecise(self):
        with self.assertRaises(ValueError):
            Fiat.parse_fiat("EUR", "0.00011")

    def test_parse_fiat_inexact(self):
        self.assertEqual(1, Fiat.parse_fiat_inexact("EUR", "0.0001").value)
        self.assertEqual(1, Fiat.parse_fiat_inexact("EUR", "0.00011").value)

    def test_parse_fiat_inexact_invalid_amount(self):
        with self.assertRaises(ValueError):
            Fiat.parse_fiat_inexact("USD", "33.xx")

    def test_to_friendly_string(self):
        self.assertEqual("1.00 EUR", Fiat.parse_fiat("EUR", "1").to_friendly_string())
        self.assertEqual("1.23 EUR", Fiat.parse_fiat("EUR", "1.23").to_friendly_string())
        self.assertEqual("0.0010 EUR", Fiat.parse_fiat("EUR", "0.001").to_friendly_string())
        self.assertEqual("-1.23 EUR", Fiat.parse_fiat("EUR", "-1.23").to_friendly_string())

    def test_to_plain_string(self):
        self.assertEqual("0.0015", Fiat.value_of("EUR", 15).to_plain_string())
        self.assertEqual("1.23", Fiat.parse_fiat("EUR", "1.23").to_plain_string())
        
        self.assertEqual("0.1", Fiat.parse_fiat("EUR", "0.1").to_plain_string())
        self.assertEqual("1.1", Fiat.parse_fiat("EUR", "1.1").to_plain_string())
        self.assertEqual("21.12", Fiat.parse_fiat("EUR", "21.12").to_plain_string())
        self.assertEqual("321.123", Fiat.parse_fiat("EUR", "321.123").to_plain_string())
        self.assertEqual("4321.1234", Fiat.parse_fiat("EUR", "4321.1234").to_plain_string())

        # check there are no trailing zeros
        self.assertEqual("1", Fiat.parse_fiat("EUR", "1.0").to_plain_string())
        self.assertEqual("2", Fiat.parse_fiat("EUR", "2.00").to_plain_string())
        self.assertEqual("3", Fiat.parse_fiat("EUR", "3.000").to_plain_string())
        self.assertEqual("4", Fiat.parse_fiat("EUR", "4.0000").to_plain_string())
        
    def test_comparing(self):
        self.assertTrue(Fiat.parse_fiat("EUR", "1.11") < (Fiat.parse_fiat("EUR", "6.66")))
        self.assertTrue(Fiat.parse_fiat("EUR", "6.66") > (Fiat.parse_fiat("EUR", "2.56")))
        self.assertTrue(Fiat.parse_fiat("EUR", "6.66") == (Fiat.parse_fiat("EUR", "6.66")))
        self.assertTrue(Fiat.parse_fiat("EUR", "6.66") != (Fiat.parse_fiat("EUR", "6.65")))

    def test_sign(self):
        self.assertTrue(Fiat.parse_fiat("EUR", "-1").is_negative())
        self.assertTrue(Fiat.parse_fiat("EUR", "-1").negate().is_positive())
        self.assertTrue(Fiat.parse_fiat("EUR", "1").is_positive())
        self.assertTrue(Fiat.parse_fiat("EUR", "0.00").is_zero())

    def test_currency_code(self):
        self.assertEqual("RUB", Fiat.parse_fiat("RUB", "66.6").currency_code)

    def test_value_fetching(self):
        fiat = Fiat.parse_fiat("USD", "666")
        self.assertEqual(6660000, fiat.value)
        self.assertEqual("6660000", str(fiat))

    def test_operations(self):
        fiat_a = Fiat.parse_fiat("USD", "666")
        fiat_b = Fiat.parse_fiat("USD", "2")

        sum_result = fiat_a.add(fiat_b)
        self.assertEqual(6680000, sum_result.value)
        self.assertEqual("USD", sum_result.currency_code)

        sub_result = fiat_a.subtract(fiat_b)
        self.assertEqual(6640000, sub_result.value)
        self.assertEqual("USD", sub_result.currency_code)

        div_result = fiat_a.divide(2)
        self.assertEqual(3330000, div_result.value)
        self.assertEqual("USD", div_result.currency_code)

        ldiv_result = fiat_a.divide(fiat_b)
        self.assertEqual(333, ldiv_result)

        mul_result = fiat_a.multiply(2)
        self.assertEqual(13320000, mul_result.value)

        fiats = fiat_a.divide_and_remainder(3)
        self.assertEqual(2, len(fiats))

        fiat1 = fiats[0]
        self.assertEqual(2220000, fiat1.value)
        self.assertEqual("USD", fiat1.currency_code)

        fiat2 = fiats[1]
        self.assertEqual(0, fiat2.value)
        self.assertEqual("USD", fiat2.currency_code)

if __name__ == '__main__':
    unittest.main()