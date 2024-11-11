import unittest

from bisq.asset.coins.dash import Dash
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DashTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Dash())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("XjNms118hx6dGyBqsrVMTbzMUmxDVijk7Y")
        self.assert_valid_address("XjNPzWfzGiY1jHUmwn9JDSVMsTs6EtZQMc")
        self.assert_valid_address("XjNPzWfzGiY1jHUmwn9JDSVMsTs6EtZQMc")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("1XnaJzoAKTNa67Fpt1tLxD5bFMcyN4tCvTT")
        self.assert_invalid_address("XnaJzoAKTNa67Fpt1tLxD5bFMcyN4tCvTTd")
        self.assert_invalid_address("XnaJzoAKTNa67Fpt1tLxD5bFMcyN4tCvTT#")


if __name__ == '__main__':
    unittest.main()