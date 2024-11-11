import unittest

from bisq.asset.tokens.augmint_euro import AugmintEuro
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class AugmintEuroTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, AugmintEuro())
    
    def test_valid_addresses(self):
        self.assert_valid_address("0x0d81d9e21bd7c5bb095535624dcb0759e64b3899")
        self.assert_valid_address("0d81d9e21bd7c5bb095535624dcb0759e64b3899")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0x65767ec6d4d3d18a200842352485cdc37cbf3a216")
        self.assert_invalid_address("0x65767ec6d4d3d18a200842352485cdc37cbf3a2g")
        self.assert_invalid_address("65767ec6d4d3d18a200842352485cdc37cbf3a2g")


if __name__ == '__main__':
    unittest.main()