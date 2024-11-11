import unittest

from bisq.asset.coins.faircoin import Faircoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class FaircoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Faircoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("fLsJC1Njap5NxSArYr5wCJbKBbTQfWikY6")
        self.assert_valid_address("FZHzHraqjty2Co7TinwcsBtPKoz5ANvgRd")
        self.assert_valid_address("fHbXBBBjU1xxEVmWEtAEwXnoBDxxsxfvxg")

    def test_invalid_addresses(self):
        self.assert_invalid_address("FLsJC1Njap5NxSArYr5wCJbKBbTQfWikY6")
        self.assert_invalid_address("fZHzHraqjty2Co7TinwcsBtPKoz5ANvgRd")
        self.assert_invalid_address("1HbXBBBjU1xxEVmWEtAEwXnoBDxxsxfvxg")


if __name__ == '__main__':
    unittest.main()