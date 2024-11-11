import unittest
from bisq.asset.coins.vertcoin import Vertcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class VertcoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Vertcoin())

    def test_valid_addresses(self):
        self.assert_valid_address("VmVwB5dxph84tbi5XqRUtfX1MfmP8WpWWL")
        self.assert_valid_address("Vt85c1QcQYE318zXqZUnjUB6fwjTrf1Xkb")
        self.assert_valid_address("33ny4vAPJHFu5Nic7uMHQrvCACYTKPFJ5p")

    def test_invalid_addresses(self):
        self.assert_invalid_address("VmVwB5dxph84tb15XqRUtfX1MfmP8WpWWW")
        self.assert_invalid_address("Vt85555555555555c1QcQYE318zXqZUnjUB6fwjTrf1Xkb")
        self.assert_invalid_address("33ny4vAPJHFu5Nic7uMHQrvCACYTKPFJ6r#")


if __name__ == "__main__":
    unittest.main()
