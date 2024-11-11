import unittest
from bisq.asset.coins.sub1x import SUB1X
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class SUB1XTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, SUB1X())

    def test_valid_addresses(self):
        self.assert_valid_address("ZDxdoVuyosZ6vY3LZAP1Z4H4eXMq2ZpLH7")
        self.assert_valid_address("ZKi6EksPCZoMi6EGXS9vWVed4NeSov2ZS4")
        self.assert_valid_address("ZT29B3yDJq1jzkCTBs4LnraM3E854MAPRm")
        self.assert_valid_address("ZZeaSimQwza3CkFWTrRPQDamZcbntf2uMG")

    def test_invalid_addresses(self):
        self.assert_invalid_address("zKi6EksPCZoMi6EGXS9vWVed4NeSov2ZS4")
        self.assert_invalid_address("ZDxdoVuyosZ6vY3LZAP1Z4H4eXMq2ZpAC7")
        self.assert_invalid_address("ZKi6EksPCZoMi6EGXS9vWVedqwfov2ZS4")
        self.assert_invalid_address("ZT29B3yDJq1jzkqwrwBs4LnraM3E854MAPRm")
        self.assert_invalid_address("ZZeaSimQwza3CkFWTqwrfQDamZcbntf2uMG")
        self.assert_invalid_address("Z23t23f")
        self.assert_invalid_address("ZZeaSimQwza3CkFWTrRPQDavZcbnta2uMGA")

if __name__ == "__main__":
    unittest.main()
