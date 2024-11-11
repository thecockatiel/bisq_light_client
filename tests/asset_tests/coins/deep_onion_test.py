import unittest

from bisq.asset.coins.deep_onion import DeepOnion
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DeepOnionTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, DeepOnion())
    
    def test_valid_addresses(self):
        self.assert_valid_address("DYQLyJ1CcxJyRBujtKdv2JDkQEkEkAzNNA")
        self.assert_valid_address("DW7YKfPgm7fdTNGyyaSVfQhY7ccBoeVK5D")
        self.assert_valid_address("DsA31xPpijxiCuTQeYMpMTQsTH1m2jTgtS")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1sA31xPpijxiCuTQeYMpMTQsTH1m2jTgtS")
        self.assert_invalid_address("DsA31xPpijxiCuTQeYMpMTQsTH1m2jTgtSd")
        self.assert_invalid_address("DsA31xPpijxiCuTQeYMpMTQsTH1m2jTgt#")


if __name__ == '__main__':
    unittest.main()