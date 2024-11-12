import unittest

from bisq.asset.tokens.tether_usderc20 import TetherUSDERC20
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class TetherUSDERC20Test(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, TetherUSDERC20())
    
    def test_valid_addresses(self):
        self.assert_valid_address("0x2a65Aca4D5fC5B5C859090a6c34d164135398226")
        self.assert_valid_address("2a65Aca4D5fC5B5C859090a6c34d164135398226")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0x2a65Aca4D5fC5B5C859090a6c34d1641353982266")
        self.assert_invalid_address("0x2a65Aca4D5fC5B5C859090a6c34d16413539822g")
        self.assert_invalid_address("2a65Aca4D5fC5B5C859090a6c34d16413539822g")


if __name__ == '__main__':
    unittest.main()