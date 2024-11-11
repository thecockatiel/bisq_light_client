import unittest

from bisq.asset.coins.litecoin_plus import LitecoinPlus
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class LitecoinPlusTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, LitecoinPlus())

    def test_valid_addresses(self):
        self.assert_valid_address("XGnikpGiuDTaxq9vPfDF9m9VfTpv4SnNN5")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW")
        self.assert_invalid_address("LgfapHEPhZbdRF9pMd5WPT35hFXcZS1USrW")
        self.assert_invalid_address("LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW")


if __name__ == "__main__":
    unittest.main()
