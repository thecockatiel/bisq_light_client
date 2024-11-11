import unittest

from bisq.asset.coins.animecoin import Animecoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class AnimecoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Animecoin())

    def test_valid_addresses(self):
        self.assert_valid_address("Aa6TDuudiNh7DRzs11wEzZWiw9QBZY3Qw1")
        self.assert_valid_address("AdsdUhnPsJwg5NvAuyxs4EsaE2GoSHohoq")
        self.assert_valid_address("4s2peLxJJ2atz1tnAKpFshnVPKTmR312fr")

    def test_invalid_addresses(self):
        self.assert_invalid_address("aa6TDuudiNh7DRzs11wEzZWiw9QBZY3Qw1")
        self.assert_invalid_address("3s2peLxJJ2atz1tnAKpFshnVPKTmR312fr")
        self.assert_invalid_address("ANNPzjj2ZYEhpyJ6p6sWeH1JXbkCSmNSd#")


if __name__ == "__main__":
    unittest.main()
