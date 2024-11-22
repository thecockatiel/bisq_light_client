import math
import unittest
from bisq.common.util.math_utils import MathUtils

class MathUtilsTest(unittest.TestCase):

    def test_rounding_double(self):
        self.assertEqual(MathUtils.round_double(1.234567, 2), 1.23)
        self.assertEqual(MathUtils.round_double(1.234567, 1), 1.2)
        self.assertEqual(MathUtils.round_double(1.234567, 0), 1.0)
        self.assertEqual(MathUtils.round_double(1.123456987654, 3), 1.123)
        self.assertEqual(MathUtils.round_double(1.123456987654, 5), 1.12346)
        self.assertEqual(MathUtils.round_double(1.123456987654, 9), 1.123456988)
        self.assertEqual(MathUtils.round_double(1.123456987654, 1), 1.1)
        self.assertEqual(MathUtils.round_double(1.55, 1), 1.6)
        self.assertEqual(MathUtils.round_double(1.49, 1), 1.5)
        self.assertEqual(MathUtils.round_double(1.51, 1), 1.5)
        
    def test_throw_on_infinities_or_nan(self):
        with self.assertRaises(ValueError):
            MathUtils.round_double(float('inf'), 2)
        with self.assertRaises(ValueError):
            MathUtils.round_double(float('-inf'), 2)
        with self.assertRaises(ValueError):
            MathUtils.round_double(float('nan'), 2)
        with self.assertRaises(ValueError):
            MathUtils.round_double(1, -1)
        with self.assertRaises(ValueError):
            MathUtils.round_double(1, -1)

if __name__ == '__main__':
    unittest.main()