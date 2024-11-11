import unittest
from bisq.asset.coins.askcoin import Askcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class AskcoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Askcoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("1")
        self.assert_valid_address("123")
        self.assert_valid_address("876982302333")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0")
        self.assert_invalid_address("038292")
        self.assert_invalid_address("")
        self.assert_invalid_address("000232320382")
        self.assert_invalid_address("1298934567890")
        self.assert_invalid_address("123abc5ab")
        self.assert_invalid_address("null")
        self.assert_invalid_address("xidjfwi23ii0")


if __name__ == '__main__':
    unittest.main()