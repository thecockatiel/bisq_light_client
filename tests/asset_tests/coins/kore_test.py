import unittest

from bisq.asset.coins.kore import Kore
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class KoreTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Kore())
    
    def test_valid_addresses(self):
        self.assert_valid_address("KViqqCDcdZn3DKJWGvmdUtmoDsxuGswzwU")
        self.assert_valid_address("KNnThWKeyJ5ibYL3JhuBacyjJxKXs2cXgv")
        self.assert_valid_address("bGcebbVyKD4PEBHeKRGX7cTydu1xRm63r4")

    def test_invalid_addresses(self):
        self.assert_invalid_address("KmVwB5dxph84tb15XqRUtfX1MfmP8WpWWW")
        self.assert_invalid_address("Kt85555555555555c1QcQYE318zXqZUnjUB6fwjTrf1Xkb")
        self.assert_invalid_address("33ny4vAPJHFu5Nic7uMHQrvCACYTKPFJ6r")


if __name__ == '__main__':
    unittest.main()