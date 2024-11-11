import unittest

from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.util.exchange_rate import ExchangeRate 

class ExchangeRateTest(unittest.TestCase):
    def test_normal_rate(self):
        rate = ExchangeRate(fiat=Fiat.parse_fiat("EUR", "500"))
        self.assertEqual("0.5", rate.coin_to_fiat(Coin.MILLICOIN()).to_plain_string())
        self.assertEqual("0.002", rate.fiat_to_coin(Fiat.parse_fiat("EUR", "1")).to_plain_string())
    
    def test_big_rate(self):
        rate = ExchangeRate(Coin.parse_coin("0.0001"), Fiat.parse_fiat("BYR", "5320387.3"))
        self.assertEqual("53203873000", rate.coin_to_fiat(Coin.COIN()).to_plain_string())
        self.assertEqual("0", rate.fiat_to_coin(Fiat.parse_fiat("BYR", "1")).to_plain_string())  # Tiny value!
    
    def test_small_rate(self):
        rate = ExchangeRate(Coin.parse_coin("1000"), Fiat.parse_fiat("XXX", "0.0001"))
        self.assertEqual("0", rate.coin_to_fiat(Coin.COIN()).to_plain_string())  # Tiny value!
        self.assertEqual("10000000", rate.fiat_to_coin(Fiat.parse_fiat("XXX", "1")).to_plain_string())
        
    def test_currency_code_mismatch(self):
        rate = ExchangeRate(fiat=Fiat.parse_fiat("EUR", "500"))
        with self.assertRaises(AssertionError):
            rate.fiat_to_coin(Fiat.parse_fiat("USD", "1"))
    
    def test_construct_missing_currency_code(self):
        with self.assertRaises(AssertionError):
            ExchangeRate(fiat=Fiat.value_of(None, 1))
    
    def test_construct_negative_coin(self):
        with self.assertRaises(AssertionError):
            ExchangeRate(coin=Coin.value_of(-1), fiat=Fiat.value_of("EUR", 1))
    
    def test_construct_negative_fiat(self):
        with self.assertRaises(AssertionError):
            ExchangeRate(fiat=Fiat.value_of("EUR", -1))
            
    # NOTE: python implementation lacks serialization capaibilities right now

if __name__ == '__main__':
    unittest.main()