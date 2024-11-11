import unittest

from bisq.asset.coins.australiacash import Australiacash
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class AustraliacashTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Australiacash())
    
    def test_valid_addresses(self):
        self.assert_valid_address("AYf2TGCoQ15HatyE99R3q9jVcXHLx1zRWW")
        self.assert_valid_address("Aahw1A79we2jUbTaamP5YALh21GSxiWTZa")
        self.assert_valid_address("ALp3R9W3QsCdqaNNcULySXN31dYvfvDkRU")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1ALp3R9W3QsCdqaNNcULySXN31dYvfvDkRU")
        self.assert_invalid_address("ALp3R9W3QsCdrqaNNcULySXN31dYvfvDkRU")
        self.assert_invalid_address("ALp3R9W3QsCdqaNNcULySXN31dYvfvDkRU#")


if __name__ == '__main__':
    unittest.main()