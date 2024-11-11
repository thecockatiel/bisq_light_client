import unittest
from bisq.asset.coins.unobtanium import Unobtanium
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class UnobtaniumTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Unobtanium())

    def test_valid_addresses(self):
        self.assert_valid_address("uXN2S9Soj4dSL7fPAuQi9twdaFmtwYndVP")
        self.assert_valid_address("uZymbhuxhfvxzc5EDdqRWrrZKvabZibBu1")
        self.assert_valid_address("uKdudT6DwojHYsBE9JWM43hRV28Rmp1Zm1")        

    def test_invalid_addresses(self):
        self.assert_invalid_address("aHu897ivzmeFuLNB6956X6gyGeVNHUBRgD")
        self.assert_invalid_address("a1HwTdCmQV3NspP2QqCGpehoFpi8NY4Zg3")
        self.assert_invalid_address("aHu897ivzmeFuLNB6956X6gyGeVNHUBRgD")        

if __name__ == "__main__":
    unittest.main()
