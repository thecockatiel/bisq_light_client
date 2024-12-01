import unittest
from decimal import Decimal

from bitcoinj.base.coin import Coin

class CoinTest(unittest.TestCase):
    def test_comparison_operations(self):
        coin1 = Coin(100)
        coin2 = Coin(200)
        coin3 = Coin(100)
        
        self.assertTrue(coin1 < coin2)
        self.assertTrue(coin2 > coin1)
        self.assertTrue(coin1 <= coin2)
        self.assertTrue(coin2 >= coin1)
        self.assertTrue(coin1 == coin3)
        self.assertTrue(coin1 != coin2)
        
    def test_arithmetic_operations(self):
        coin1 = Coin(100)
        coin2 = Coin(50)
        
        self.assertEqual(Coin(150), coin1 + coin2)
        self.assertEqual(Coin(50), coin1 - coin2)
        self.assertEqual(Coin(200), coin1 * 2)
        self.assertEqual(Coin(50), coin1 / 2)
        
    def test_static_factories(self):
        self.assertEqual(Coin(100_000_000), Coin.COIN())
        self.assertEqual(Coin(0), Coin.ZERO())
        self.assertEqual(Coin(1_000_000), Coin.CENT())
        self.assertEqual(Coin(100_000), Coin.MILLICOIN())
        self.assertEqual(Coin(100), Coin.MICROCOIN())
        self.assertEqual(Coin(1), Coin.SATOSHI())
        
    def test_value_of_methods(self):
        self.assertEqual(Coin(100_000_000), Coin.value_of(1, 0))  # 1 BTC, 0 cents
        self.assertEqual(Coin(1_000_000), Coin.value_of(0, 1))    # 0 BTC, 1 cent
        self.assertEqual(Coin(101_000_000), Coin.value_of(1, 1))  # 1 BTC, 1 cent
        
        with self.assertRaises(ValueError):
            Coin.value_of(1, 100)  # cents must be below 100
        with self.assertRaises(ValueError):
            Coin.value_of(1, -1)   # cents cannot be negative
            
    def test_conversion_methods(self):
        # Test BTC to satoshi conversion
        self.assertEqual(100_000_000, Coin.btc_to_satoshi(Decimal('1.0')))
        self.assertEqual(1, Coin.btc_to_satoshi(Decimal('0.00000001')))
        
        # Test satoshi to BTC conversion
        self.assertEqual(Decimal('1.0'), Coin.satoshi_to_btc(100_000_000))
        self.assertEqual(Decimal('0.00000001'), Coin.satoshi_to_btc(1))
        
        # Test string parsing
        self.assertEqual(Coin(100_000_000), Coin.parse_coin('1.0'))
        self.assertEqual(Coin(1), Coin.parse_coin('0.00000001'))
        
        with self.assertRaises(ValueError):
            Coin.parse_coin('invalid')
            
    def test_comparison_methods(self):
        coin = Coin(100)
        self.assertTrue(coin.is_positive())
        self.assertFalse(coin.is_negative())
        self.assertFalse(coin.is_zero())
        
        neg_coin = Coin(-100)
        self.assertFalse(neg_coin.is_positive())
        self.assertTrue(neg_coin.is_negative())
        self.assertFalse(neg_coin.is_zero())
        
        zero_coin = Coin(0)
        self.assertFalse(zero_coin.is_positive())
        self.assertFalse(zero_coin.is_negative())
        self.assertTrue(zero_coin.is_zero())
        
    def test_bitwise_operations(self):
        coin = Coin(100)
        self.assertEqual(Coin(400), coin.shift_left(2))
        self.assertEqual(Coin(25), coin.shift_right(2))

if __name__ == '__main__':
    unittest.main()