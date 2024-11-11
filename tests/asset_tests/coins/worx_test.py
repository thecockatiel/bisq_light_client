import unittest
from bisq.asset.coins.worx import WORX
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class WORXTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, WORX())

    def test_valid_addresses(self):
        self.assert_valid_address("WgeBjv4PkmNnsUZ6QqhhT3ynEaqr3xDWuS")
        self.assert_valid_address("WQDes3h9GBa72R9govQCic3f38m566Jydo")
        self.assert_valid_address("WeNnnz8KFgmipcLhpbXSM9HT37pSqqeVbk")
        self.assert_valid_address("WNzf7fZgc2frhBGqVvhVhYpSBMWd2WE6x5")

    def test_invalid_addresses(self):
        self.assert_invalid_address("WgeBjv4PksmNnsUZ6QqhhT3ynEaqr3xDWuS")
        self.assert_invalid_address("W2QDes3h9GBa72R9govQCic3f38m566Jydo")
        self.assert_invalid_address("WeNnnz8KFgmipcLhpbXSM9HT37pSqqeVbk3")
        self.assert_invalid_address("WNzf7fZgc2frhBGqVvhVhYpSBMWd2WE6x54")


if __name__ == "__main__":
    unittest.main()
