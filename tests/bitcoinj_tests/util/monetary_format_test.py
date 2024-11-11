import unittest 

from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.base.utils.monetary_format import MonetaryFormat

class TestMonetaryFormat(unittest.TestCase):
    def setUp(self):
        self.no_code = MonetaryFormat.BTC().no_code()
        self.ONE_EURO = Fiat.parse_fiat("EUR", "1")  # Class constant

    def test_signs(self):
        self.assertEqual("-1.00", self.no_code.format(Coin.COIN().negate()))
        self.assertEqual("@1.00", self.no_code.with_negative_sign('@').format(Coin.COIN().negate()))
        self.assertEqual("1.00", self.no_code.format(Coin.COIN()))
        self.assertEqual("+1.00", self.no_code.with_positive_sign('+').format(Coin.COIN()))

    def test_digits(self):
        self.assertEqual("١٢.٣٤٥٦٧٨٩٠", self.no_code.digits('\u0660').format(Coin.value_of(1234567890)))

    def test_decimal_mark(self):
        self.assertEqual("1.00", self.no_code.format(Coin.COIN()))
        self.assertEqual("1,00", self.no_code.with_decimal_mark(',').format(Coin.COIN()))

    def format(self, coin, shift, min_decimals, *decimal_groups):
        return self.no_code.with_shift(shift).with_min_decimals(min_decimals).optional_decimals(decimal_groups).format(coin)
    
    def test_grouping(self):
        self.assertEqual("0.1", self.format(Coin.parse_coin("0.1"), 0, 1, 2, 3))
        self.assertEqual("0.010", self.format(Coin.parse_coin("0.01"), 0, 1, 2, 3))
        self.assertEqual("0.001", self.format(Coin.parse_coin("0.001"), 0, 1, 2, 3))
        self.assertEqual("0.000100", self.format(Coin.parse_coin("0.0001"), 0, 1, 2, 3))
        self.assertEqual("0.000010", self.format(Coin.parse_coin("0.00001"), 0, 1, 2, 3))
        self.assertEqual("0.000001", self.format(Coin.parse_coin("0.000001"), 0, 1, 2, 3))

    def test_btc_rounding(self):
        self.assertEqual("0", self.format(Coin.ZERO(), 0, 0))
        self.assertEqual("0.00", self.format(Coin.ZERO(), 0, 2))

        self.assertEqual("1", self.format(Coin.COIN(), 0, 0))
        self.assertEqual("1.0", self.format(Coin.COIN(), 0, 1))
        self.assertEqual("1.00", self.format(Coin.COIN(), 0, 2, 2))
        self.assertEqual("1.00", self.format(Coin.COIN(), 0, 2, 2, 2))
        self.assertEqual("1.00", self.format(Coin.COIN(), 0, 2, 2, 2, 2))
        self.assertEqual("1.000", self.format(Coin.COIN(), 0, 3))
        self.assertEqual("1.0000", self.format(Coin.COIN(), 0, 4))

        just_not = Coin.COIN().subtract(Coin.SATOSHI())
        self.assertEqual("1", self.format(just_not, 0, 0))
        self.assertEqual("1.0", self.format(just_not, 0, 1))
        self.assertEqual("1.00", self.format(just_not, 0, 2, 2))
        self.assertEqual("1.00", self.format(just_not, 0, 2, 2, 2))
        self.assertEqual("0.99999999", self.format(just_not, 0, 2, 2, 2, 2))
        self.assertEqual("1.000", self.format(just_not, 0, 3))
        self.assertEqual("1.0000", self.format(just_not, 0, 4))

        slightly_more = Coin.COIN().add(Coin.SATOSHI())
        self.assertEqual("1", self.format(slightly_more, 0, 0))
        self.assertEqual("1.0", self.format(slightly_more, 0, 1))
        self.assertEqual("1.00", self.format(slightly_more, 0, 2, 2))
        self.assertEqual("1.00", self.format(slightly_more, 0, 2, 2, 2))
        self.assertEqual("1.00000001", self.format(slightly_more, 0, 2, 2, 2, 2))
        self.assertEqual("1.000", self.format(slightly_more, 0, 3))
        self.assertEqual("1.0000", self.format(slightly_more, 0, 4))

        pivot = Coin.COIN().add(Coin.SATOSHI().multiply(5))
        self.assertEqual("1.00000005", self.format(pivot, 0, 8))
        self.assertEqual("1.00000005", self.format(pivot, 0, 7, 1))
        self.assertEqual("1.0000001", self.format(pivot, 0, 7))

        value = Coin.value_of(1122334455667788)
        self.assertEqual("11223345", self.format(value, 0, 0))
        self.assertEqual("11223344.6", self.format(value, 0, 1))
        self.assertEqual("11223344.5567", self.format(value, 0, 2, 2))
        self.assertEqual("11223344.556678", self.format(value, 0, 2, 2, 2))
        self.assertEqual("11223344.55667788", self.format(value, 0, 2, 2, 2, 2))
        self.assertEqual("11223344.557", self.format(value, 0, 3))
        self.assertEqual("11223344.5567", self.format(value, 0, 4))
        
    def test_mbtc_rounding(self):
        self.assertEqual("0", self.format(Coin.ZERO(), 3, 0))
        self.assertEqual("0.00", self.format(Coin.ZERO(), 3, 2))

        self.assertEqual("1000", self.format(Coin.COIN(), 3, 0))
        self.assertEqual("1000.0", self.format(Coin.COIN(), 3, 1))
        self.assertEqual("1000.00", self.format(Coin.COIN(), 3, 2))
        self.assertEqual("1000.00", self.format(Coin.COIN(), 3, 2, 2))
        self.assertEqual("1000.000", self.format(Coin.COIN(), 3, 3))
        self.assertEqual("1000.0000", self.format(Coin.COIN(), 3, 4))

        just_not = Coin.COIN().subtract(Coin.SATOSHI().multiply(10))
        self.assertEqual("1000", self.format(just_not, 3, 0))
        self.assertEqual("1000.0", self.format(just_not, 3, 1))
        self.assertEqual("1000.00", self.format(just_not, 3, 2))
        self.assertEqual("999.9999", self.format(just_not, 3, 2, 2))
        self.assertEqual("1000.000", self.format(just_not, 3, 3))
        self.assertEqual("999.9999", self.format(just_not, 3, 4))

        slightly_more = Coin.COIN().add(Coin.SATOSHI().multiply(10))
        self.assertEqual("1000", self.format(slightly_more, 3, 0))
        self.assertEqual("1000.0", self.format(slightly_more, 3, 1))
        self.assertEqual("1000.00", self.format(slightly_more, 3, 2))
        self.assertEqual("1000.000", self.format(slightly_more, 3, 3))
        self.assertEqual("1000.0001", self.format(slightly_more, 3, 2, 2))
        self.assertEqual("1000.0001", self.format(slightly_more, 3, 4))

        pivot = Coin.COIN().add(Coin.SATOSHI().multiply(50))
        self.assertEqual("1000.0005", self.format(pivot, 3, 4))
        self.assertEqual("1000.0005", self.format(pivot, 3, 3, 1))
        self.assertEqual("1000.001", self.format(pivot, 3, 3))

        value = Coin.value_of(1122334455667788)
        self.assertEqual("11223344557", self.format(value, 3, 0))
        self.assertEqual("11223344556.7", self.format(value, 3, 1))
        self.assertEqual("11223344556.68", self.format(value, 3, 2))
        self.assertEqual("11223344556.6779", self.format(value, 3, 2, 2))
        self.assertEqual("11223344556.678", self.format(value, 3, 3))
        self.assertEqual("11223344556.6779", self.format(value, 3, 4))

    def test_ubtc_rounding(self):
        self.assertEqual("0", self.format(Coin.ZERO(), 6, 0))
        self.assertEqual("0.00", self.format(Coin.ZERO(), 6, 2))

        self.assertEqual("1000000", self.format(Coin.COIN(), 6, 0))
        self.assertEqual("1000000", self.format(Coin.COIN(), 6, 0, 2))
        self.assertEqual("1000000.0", self.format(Coin.COIN(), 6, 1))
        self.assertEqual("1000000.00", self.format(Coin.COIN(), 6, 2))

        just_not = Coin.COIN().subtract(Coin.SATOSHI())
        self.assertEqual("1000000", self.format(just_not, 6, 0))
        self.assertEqual("999999.99", self.format(just_not, 6, 0, 2))
        self.assertEqual("1000000.0", self.format(just_not, 6, 1))
        self.assertEqual("999999.99", self.format(just_not, 6, 2))

        slightly_more = Coin.COIN().add(Coin.SATOSHI())
        self.assertEqual("1000000", self.format(slightly_more, 6, 0))
        self.assertEqual("1000000.01", self.format(slightly_more, 6, 0, 2))
        self.assertEqual("1000000.0", self.format(slightly_more, 6, 1))
        self.assertEqual("1000000.01", self.format(slightly_more, 6, 2))

        pivot = Coin.COIN().add(Coin.SATOSHI().multiply(5))
        self.assertEqual("1000000.05", self.format(pivot, 6, 2))
        self.assertEqual("1000000.05", self.format(pivot, 6, 0, 2))
        self.assertEqual("1000000.1", self.format(pivot, 6, 1))
        self.assertEqual("1000000.1", self.format(pivot, 6, 0, 1))

        value = Coin.value_of(1122334455667788)
        self.assertEqual("11223344556678", self.format(value, 6, 0))
        self.assertEqual("11223344556677.88", self.format(value, 6, 2))
        self.assertEqual("11223344556677.9", self.format(value, 6, 1))
        self.assertEqual("11223344556677.88", self.format(value, 6, 2))

    def test_sat(self):
        self.assertEqual("0", self.format(Coin.ZERO(), 8, 0))
        self.assertEqual("100000000", self.format(Coin.COIN(), 8, 0))
        self.assertEqual("2100000000000000", self.format(Coin.COIN().multiply(21_000_000), 8, 0))
        
    def format_repeat(self, coin: Coin, decimals: int, repetitions: int):
        return self.no_code.with_min_decimals(0).repeat_optional_decimals(decimals, repetitions).format(coin)

    def test_repeat_optional_decimals(self):
        self.assertEqual("0.00000001", self.format_repeat(Coin.SATOSHI(), 2, 4))
        self.assertEqual("0.00000010", self.format_repeat(Coin.SATOSHI().multiply(10), 2, 4))
        self.assertEqual("0.01", self.format_repeat(Coin.CENT(), 2, 4))
        self.assertEqual("0.10", self.format_repeat(Coin.CENT().multiply(10), 2, 4))

        self.assertEqual("0", self.format_repeat(Coin.SATOSHI(), 2, 2))
        self.assertEqual("0", self.format_repeat(Coin.SATOSHI().multiply(10), 2, 2))
        self.assertEqual("0.01", self.format_repeat(Coin.CENT(), 2, 2))
        self.assertEqual("0.10", self.format_repeat(Coin.CENT().multiply(10), 2, 2))

        self.assertEqual("0", self.format_repeat(Coin.CENT(), 2, 0))
        self.assertEqual("0", self.format_repeat(Coin.CENT().multiply(10), 2, 0))
        
    def test_standard_codes(self):
        self.assertEqual("BTC 0.00", str(MonetaryFormat.BTC().format(Coin.ZERO())))
        self.assertEqual("mBTC 0.00", str(MonetaryFormat.MBTC().format(Coin.ZERO())))
        self.assertEqual("µBTC 0", str(MonetaryFormat.UBTC().format(Coin.ZERO())))
        self.assertEqual("sat 0", str(MonetaryFormat.SAT().format(Coin.ZERO())))

    def test_standard_symbol(self):
        self.assertEqual("₿ 0.00", str(MonetaryFormat(True).format(Coin.ZERO())))

    def test_custom_code(self):
        self.assertEqual("dBTC 0", str(MonetaryFormat.UBTC().code(1, "dBTC").with_shift(1).format(Coin.ZERO())))

    def test_no_code(self):
        # Test clearing all codes
        self.assertEqual("0", str(MonetaryFormat.UBTC().no_code().with_shift(0).format(Coin.ZERO())))
        # Test setting code after clearing
        self.assertEqual("dBTC 0", str(MonetaryFormat.UBTC().no_code().code(1, "dBTC").with_shift(1).format(Coin.ZERO())))

    def test_code_orientation(self):
        self.assertEqual("BTC 0.00", str(MonetaryFormat.BTC().prefix_code().format(Coin.ZERO())))
        self.assertEqual("0.00 BTC", str(MonetaryFormat.BTC().postfix_code().format(Coin.ZERO())))

    def test_code_separator(self):
        self.assertEqual("BTC@0.00", str(MonetaryFormat.BTC().with_code_separator('@').format(Coin.ZERO())))

    def test_missing_code(self):
        with self.assertRaises(ValueError):  # Python uses ValueError instead of NumberFormatException
            MonetaryFormat.UBTC().with_shift(1).format(Coin.ZERO())

    def test_with_locale(self):
        value = Coin.value_of(-1234567890)
        self.assertEqual("-12.34567890", str(self.no_code.with_locale('en_US').format(value)))
        self.assertEqual("-12,34567890", str(self.no_code.with_locale('de_DE').format(value)))

    @unittest.skip("non-determinism between Python implementations")
    def test_with_locale_devanagari(self):
        value = Coin.value_of(-1234567890)
        self.assertEqual("-१२.३४५६७८९०", str(self.no_code.with_locale('hi_IN').format(value)))
    
    def test_parse(self):
        self.assertEqual(Coin.COIN(), self.no_code.parse("1"))
        self.assertEqual(Coin.COIN(), self.no_code.parse("1."))
        self.assertEqual(Coin.COIN(), self.no_code.parse("1.0"))
        self.assertEqual(Coin.COIN(), self.no_code.with_decimal_mark(',').parse("1,0"))
        self.assertEqual(Coin.COIN(), self.no_code.parse("01.0000000000"))
        self.assertEqual(Coin.COIN(), self.no_code.with_positive_sign('+').parse("+1.0"))
        self.assertEqual(Coin.COIN().negate(), self.no_code.parse("-1"))
        self.assertEqual(Coin.COIN().negate(), self.no_code.parse("-1.0"))

        self.assertEqual(Coin.CENT(), self.no_code.parse(".01"))

        self.assertEqual(Coin.MILLICOIN(), MonetaryFormat.MBTC().parse("1"))
        self.assertEqual(Coin.MILLICOIN(), MonetaryFormat.MBTC().parse("1.0"))
        self.assertEqual(Coin.MILLICOIN(), MonetaryFormat.MBTC().parse("01.0000000000"))
        self.assertEqual(Coin.MILLICOIN(), MonetaryFormat.MBTC().with_positive_sign('+').parse("+1.0"))
        self.assertEqual(Coin.MILLICOIN().negate(), MonetaryFormat.MBTC().parse("-1"))
        self.assertEqual(Coin.MILLICOIN().negate(), MonetaryFormat.MBTC().parse("-1.0"))

        self.assertEqual(Coin.MICROCOIN(), MonetaryFormat.UBTC().parse("1"))
        self.assertEqual(Coin.MICROCOIN(), MonetaryFormat.UBTC().parse("1.0"))
        self.assertEqual(Coin.MICROCOIN(), MonetaryFormat.UBTC().parse("01.0000000000"))
        self.assertEqual(Coin.MICROCOIN(), MonetaryFormat.UBTC().with_positive_sign('+').parse("+1.0"))
        self.assertEqual(Coin.MICROCOIN().negate(), MonetaryFormat.UBTC().parse("-1"))
        self.assertEqual(Coin.MICROCOIN().negate(), MonetaryFormat.UBTC().parse("-1.0"))

        self.assertEqual(Coin.SATOSHI(), MonetaryFormat.SAT().parse("1"))
        self.assertEqual(Coin.SATOSHI(), MonetaryFormat.SAT().parse("01"))
        self.assertEqual(Coin.SATOSHI(), MonetaryFormat.SAT().with_positive_sign('+').parse("+1"))
        self.assertEqual(Coin.SATOSHI().negate(), MonetaryFormat.SAT().parse("-1"))

        # Note: unreliable Devanagari test
        self.assertEqual(Coin.CENT(), self.no_code.with_locale('hi_IN').parse(".०१"))
        
    def test_parse_invalid_empty(self):
        with self.assertRaises(ValueError):
            self.no_code.parse("")

    def test_parse_invalid_whitespace_before(self):
        with self.assertRaises(ValueError):
            self.no_code.parse(" 1")

    def test_parse_invalid_whitespace_sign(self):
        with self.assertRaises(ValueError):
            self.no_code.parse("- 1")

    def test_parse_invalid_whitespace_after(self):
        with self.assertRaises(ValueError):
            self.no_code.parse("1 ")

    def test_parse_invalid_multiple_decimal_marks(self):
        with self.assertRaises(ValueError):
            self.no_code.parse("1.0.0")

    def test_parse_invalid_decimal_mark(self):
        with self.assertRaises(ValueError):
            self.no_code.with_decimal_mark(',').parse("1.0")

    def test_parse_invalid_positive_sign(self):
        with self.assertRaises(ValueError):
            self.no_code.with_positive_sign('@').parse("+1.0")

    def test_parse_invalid_negative_sign(self):
        with self.assertRaises(ValueError):
            self.no_code.with_negative_sign('@').parse("-1.0")

    def test_fiat(self):
        self.assertEqual(self.ONE_EURO, self.no_code.parse_fiat("EUR", "1"))

    def test_equals(self):
        mf1 = MonetaryFormat(True)
        mf2 = MonetaryFormat(True)
        self.assertEqual(mf1, mf2)

    def test_hash_code(self):
        mf1 = MonetaryFormat(True)
        mf2 = MonetaryFormat(True)
        self.assertEqual(hash(mf1), hash(mf2))

    def test_equals_coin(self):
        mf1 = Coin(1)
        mf2 = Coin(1)
        mf3 = Coin(2)
        self.assertEqual(mf1, mf2)
        self.assertNotEqual(mf1, mf3)

    def test_hash_code_coin(self):
        mf1 = Coin(1)
        mf2 = Coin(1)
        mf3 = Coin(2)
        self.assertEqual(hash(mf1), hash(mf2))
        self.assertNotEqual(hash(mf1), hash(mf3))


if __name__ == '__main__':
    unittest.main()