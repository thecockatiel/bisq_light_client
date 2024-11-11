import unittest

from bisq.asset.coins.cts_coin import CTSCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CTSCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, CTSCoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("Ti6S7JhtxKjSytZDmyMV4pVNVAPeiVsnpT")
        self.assert_valid_address("TwzRDeNSPcJvquuGu7WxxH3RhXBR1VPYHZ")
        self.assert_valid_address("TgYGQJd5TEzDRkyXt1tCvUnrbWBu38C8YK")

    def test_invalid_addresses(self):
        self.assert_invalid_address("ti6S7JhtxKjSytZDmyMV4pVNVAPeiVsnpT")
        self.assert_invalid_address("2i6S7JhtxKjSytZDmyMV4pVNVAPeiVsnpT")
        self.assert_invalid_address("Ti6S7JhtxKjSytZDmyMV4pVNVAPeiVsnp")


if __name__ == '__main__':
    unittest.main()