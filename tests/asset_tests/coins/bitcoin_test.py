import unittest

from bisq.asset.coins.bitcoin import Bitcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CoinsTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Bitcoin.Mainnet())
    
    def test_valid_addresses(self):
        self.assert_valid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem")
        self.assert_valid_address("3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX")
        self.assert_valid_address("1111111111111111111114oLvT2")
        self.assert_valid_address("1BitcoinEaterAddressDontSendf59kuE")

    def test_invalid_addresses(self):
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhemqq")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYheO")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhek#")


if __name__ == '__main__':
    unittest.main()