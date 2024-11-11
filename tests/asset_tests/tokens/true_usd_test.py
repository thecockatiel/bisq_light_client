import unittest

from bisq.asset.tokens.true_usd import TrueUSD
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class TrueUSDTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, TrueUSD())
    
    def test_valid_addresses(self):
        self.assert_valid_address("0xa23579c2f7b462e5fb2e92f8cf02971fe4de4f82")
        self.assert_valid_address("0xdb59b63738e27e6d689c9d72c92c7a12f22161bb")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0x2a65Aca4D5fC5B5C859090a6c34d1641353982266")
        self.assert_invalid_address("0x2a65Aca4D5fC5B5C859090a6c34d16413539822g")
        self.assert_invalid_address("2a65Aca4D5fC5B5C859090a6c34d16413539822g")


if __name__ == '__main__':
    unittest.main()