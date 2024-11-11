import unittest
from bisq.asset.coins.pinkcoin import Pinkcoin 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class PinkcoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Pinkcoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("2KZEgvipDn5EkDAFB8UR8nVXuKuKt8rmgH")
        self.assert_valid_address("2KVgwafcbw9LcJngqAzxu8UKpQSRwNhtTH")
        self.assert_valid_address("2TPDcXRRmvTxJQ4V8xNhP1KmrTmH9KKCkg")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("PPo1gCi4xoC87gZZsnU2Uj6vSgZAAD9com")
        self.assert_invalid_address("z4Vg3S5pJEJY45tHX7u6X1r9tv2DEvCShi2")
        self.assert_invalid_address("1dQT9U73rNmomYkkxQwcNYhfQr9yy4Ani")


if __name__ == '__main__':
    unittest.main()