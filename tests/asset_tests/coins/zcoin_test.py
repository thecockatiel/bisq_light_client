import unittest
from bisq.asset.coins.zcoin import Zcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class ZcoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Zcoin())

    def test_valid_addresses(self):
        self.assert_valid_address("aHu897ivzmeFuLNB6956X6gyGeVNHUBRgD")
        self.assert_valid_address("a1HwTdCmQV3NspP2QqCGpehoFpi8NY4Zg3")
        self.assert_valid_address("aHu897ivzmeFuLNB6956X6gyGeVNHUBRgD")    

    def test_invalid_addresses(self):
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")
        self.assert_invalid_address("N22FRU9f3fx7Hty641D5cg95kRK6S3sbf3")
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")        


if __name__ == "__main__":
    unittest.main()
