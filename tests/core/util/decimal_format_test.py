import unittest
from bisq.core.util.decimal_format import DecimalFormat

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

if __name__ == '__main__':
    unittest.main()
