import unittest

from bisq.asset.coins.liquid_bitcoin import LiquidBitcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class LiquidBitcoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, LiquidBitcoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("VJL6mu5gqT4pRzpd28Y6aXg9murwJpd25EBwMtrnCN82n6z6i5kMLKnN63nyaCgRuJWZu4EFFV7gp9Yb")
        self.assert_valid_address("Gq3AeVacy6EUWSJKsV4NScyYKvnM6Gf8We")

    def test_invalid_addresses(self):
        self.assert_invalid_address("lq1qqgu6g99aa4y7fly26gwj3k69t2kgx8eshn8gqacsul9yhpcgtvweyzuqt6cn3fjawvwaluq6ls6t9qnvg4jgwffyycwmgqh0h")
        self.assert_invalid_address("lq1qqgu6g99aa4y7fly26gwj3k69t2kgx8eshn8gqacsul9yhpcgtvweyzuqt6cn3fjawvwaluq6ls6t9qnvg4jgwffyycwmgqsdf")


if __name__ == '__main__':
    unittest.main()