import unittest
from bisq.asset.coins.noir import Noir
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class NoirTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Noir())
    
    def test_valid_addresses(self):
        self.assert_valid_address("ZMZ6M64FiFjPjmzXRf7xBuyarorUmT8uyG")
        self.assert_valid_address("ZHoMM3vccwGrAQocmmp9ZHA7Gjg9Uqkok7")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("")
        self.assert_invalid_address("21HQQgsvLTgN9xD9hNmAgAreakzVzQUSLSHa")
        self.assert_invalid_address("ZHoMM3vccwGrAQocmmp9ZHA7Gjg9Uqkok7*")
        self.assert_invalid_address("ZHoMM3vccwGrAQocmmp9ZHA7Gjg9Uqkok7#jHt5jtP")


if __name__ == '__main__':
    unittest.main()