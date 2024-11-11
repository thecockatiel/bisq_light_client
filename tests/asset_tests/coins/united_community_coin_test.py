import unittest
from bisq.asset.coins.united_community_coin import UnitedCommunityCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class UnitedCommunityCoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, UnitedCommunityCoin())

    def test_valid_addresses(self):
        self.assert_valid_address("UX3DVuoiNR9Uwa22NLehu8yVKecjFKn4ii")
        self.assert_valid_address("URqRRRFY7D6drJCput5UjTRUQYEL8npUwk")
        self.assert_valid_address("Uha1WUkuYtW9Uapme2E46PBz2sBkM9qV9w")

    def test_invalid_addresses(self):
        self.assert_invalid_address("UX3DVuoiNR90wa22NLehu8yVKecjFKn4ii")
        self.assert_invalid_address("URqRRRFY7D6drJCput5UjTRUQYaEL8npUwk")
        self.assert_invalid_address("Uha1WUkuYtW9Uapme2E46PBz2$BkM9qV9w")

if __name__ == "__main__":
    unittest.main()
