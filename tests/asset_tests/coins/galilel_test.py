import unittest
 
from bisq.asset.coins.galilel import Galilel
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class GalilelTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Galilel())
    
    def test_valid_addresses(self):
        self.assert_valid_address("UVwXGh5B1NZbYdgWThqf2cLdkEupVXEVNi")
        self.assert_valid_address("UbNJbC1hZgBH5tQ4HyrrQMEPswKxwwfziw")
        self.assert_valid_address("UgqDDV8aekEXFP7BWLmTNpSQfk7uVk1jCF")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1UgqDDV8aekEXFP7BWLmTNpSQfk7uVk1jCF")
        self.assert_invalid_address("UgqDDV8aekEXFP7BWLmTNpSQfk7uVk1jCFd")
        self.assert_invalid_address("UgqDDV8aekEXFP7BWLmTNpSQfk7uVk1jCF#")


if __name__ == '__main__':
    unittest.main()