import unittest

from bisq.asset.coins.dogecoin import Dogecoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DogecoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Dogecoin())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("DEa7damK8MsbdCJztidBasZKVsDLJifWfE")
        self.assert_valid_address("DNkkfdUvkCDiywYE98MTVp9nQJTgeZAiFr")
        self.assert_valid_address("DDWUYQ3GfMDj8hkx8cbnAMYkTzzAunAQxg")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("1DDWUYQ3GfMDj8hkx8cbnAMYkTzzAunAQxg")
        self.assert_invalid_address("DDWUYQ3GfMDj8hkx8cbnAMYkTzzAunAQxgs")
        self.assert_invalid_address("DDWUYQ3GfMDj8hkx8cbnAMYkTzzAunAQxg#")


if __name__ == '__main__':
    unittest.main()