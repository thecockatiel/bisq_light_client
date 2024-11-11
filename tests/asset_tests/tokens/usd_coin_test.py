import unittest

from bisq.asset.tokens.usd_coin import USDCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class USDCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, USDCoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("0xb86bb5fc804768db34f1a37da8b719e19af9dffd")
        self.assert_valid_address("0xea82afd93ebfc4f6564f3e5bd823cdef710f75dd")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0x2a65Aca4D5fC5B5C859090a6c34d1641353982266")
        self.assert_invalid_address("0x2a65Aca4D5fC5B5C859090a6c34d16413539822g")
        self.assert_invalid_address("2a65Aca4D5fC5B5C859090a6c34d16413539822g")


if __name__ == '__main__':
    unittest.main()