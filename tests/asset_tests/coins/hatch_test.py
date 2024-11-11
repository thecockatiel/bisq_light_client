import unittest

from bisq.asset.coins.hatch import Hatch
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class HatchTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Hatch())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("XgUfhrcfKWTVprA1GGhTggAA3VVQy1xqNp")
        self.assert_valid_address("Xo88XjP8RD2w3k7Fd16UT62y3oNcjbv4bz")
        self.assert_valid_address("XrA7ZGDLQkiLwUsfKT6y6tLrYjsvRLrZQG")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("1XrA7ZGDLQkiLwUsfKT6y6tLrYjsvRLrZQG")
        self.assert_invalid_address("XrA7ZGDLQkiLwUsfKT6y6tLrYjsvRLrZQGd")
        self.assert_invalid_address("XrA7ZGDLQkiLwUsfKT6y6tLrYjsvRLrZQG#")


if __name__ == '__main__':
    unittest.main()