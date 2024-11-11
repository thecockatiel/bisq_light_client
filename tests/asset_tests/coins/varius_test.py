import unittest
from bisq.asset.coins.varius import VARIUS
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class VARIUSTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, VARIUS())

    def test_valid_addresses(self):
        self.assert_valid_address("VL85MGBCSfnSeiLxuQwXuvxHArzfr1574H")
        self.assert_valid_address("VBKxFQULC6bjzWdb2PhZyoRdePq8fs55fi")
        self.assert_valid_address("VXwmVvzX6KMqfkBJXRXu4VUbgzPhLKdBSq")

    def test_invalid_addresses(self):
        self.assert_invalid_address("xLfnSeiLxuQwXuvxHArzfr1574H")
        self.assert_invalid_address("BBKzWdb2PhZyoRdePq8fs55fi")
        self.assert_invalid_address("vXwmVvzX6KMqfkBJXRXu4VUbgzPhLKdBSq")


if __name__ == "__main__":
    unittest.main()
