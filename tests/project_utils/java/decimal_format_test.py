import unittest
from utils.java.decimal_format import DecimalFormat
from bisq.core.util.volume_util import VolumeUtil

class TestDecimalFormat(unittest.TestCase):
    def test_default_pattern(self):
        df = DecimalFormat()
        self.assertEqual("123.44", df.format(123.44))
        self.assertEqual("123.46", df.format(123.46))
        self.assertEqual("0", df.format(None))

    def test_custom_pattern(self):
        df = DecimalFormat("#.##")
        self.assertEqual("123.49", df.format(123.49))
        self.assertEqual("123.5", df.format(123.50))
        self.assertEqual("123.51", df.format(123.51))
        self.assertEqual("123.51", df.format(123.509))
        self.assertEqual("123.5", df.format(123.501))

    def test_minimum_fraction_digits(self):
        df = DecimalFormat("#.#")
        df.set_minimum_fraction_digits(2)
        self.assertEqual("123.40", df.format(123.4))
        self.assertEqual("123.00", df.format(123))

    def test_maximum_fraction_digits(self):
        df = DecimalFormat("#.####")
        df.set_maximum_fraction_digits(2)
        self.assertEqual("123.46", df.format(123.4567))
        self.assertEqual("123.45", df.format(123.454))

    def test_min_max_fraction_interaction(self):
        df = DecimalFormat("#.####")
        df.set_maximum_fraction_digits(3)
        df.set_minimum_fraction_digits(2)
        self.assertEqual("123.455", df.format(123.45468))

    def test_zero_fractions(self):
        df = DecimalFormat("#.#")
        df.set_minimum_fraction_digits(0)
        df.set_maximum_fraction_digits(2)
        self.assertEqual("123", df.format(123.0))
        self.assertEqual("123.4", df.format(123.4))
        self.assertEqual("123.45", df.format(123.454))

    def test_grouping(self):
        df = DecimalFormat("#.##")
        df.grouping_used = True
        self.assertEqual("1,234.56", df.format(1234.56))
        self.assertEqual("1,234,567.89", df.format(1234567.89))
        self.assertEqual("-1,234.56", df.format(-1234.56))
        self.assertEqual("999", df.format(999))
        self.assertEqual("9,999", df.format(9999))

    def test_custom_grouping_size(self):
        df = DecimalFormat("#.##")
        df.grouping_used = True
        df.grouping_size = 4
        self.assertEqual("12,3456.78", df.format(123456.78))
        self.assertEqual("1,2345,6789.01", df.format(123456789.01))
        self.assertEqual("-1,2345,6789.01", df.format(-123456789.01))

    def test_sophisticated_format(self):
        self.assertEqual("12.341M USD", VolumeUtil.format_large_fiat_with_unit_postfix(12341234.1234, "USD"))
        self.assertEqual("123.123 USD", VolumeUtil.format_large_fiat_with_unit_postfix(123.1234, "USD"))
        self.assertEqual("12.123 USD", VolumeUtil.format_large_fiat_with_unit_postfix(12.123412341234, "USD"))
        self.assertEqual("123.412B USD", VolumeUtil.format_large_fiat_with_unit_postfix(123412341234.1234, "USD"))

if __name__ == '__main__':
    unittest.main()
