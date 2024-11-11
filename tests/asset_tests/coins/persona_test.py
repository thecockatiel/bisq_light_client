import unittest
from bisq.asset.coins.persona import Persona 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class PersonaTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Persona())
    
    def test_valid_addresses(self):
        self.assert_valid_address("PV5PbsyhkM1RkN41QiSXy7cisbZ4kBzm51")
        self.assert_valid_address("PJACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("")
        self.assert_invalid_address("LJACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")
        self.assert_invalid_address("TJACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")
        self.assert_invalid_address("PJACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zAA")
        self.assert_invalid_address("PlACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")
        self.assert_invalid_address("PIACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")
        self.assert_invalid_address("POACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")
        self.assert_invalid_address("P0ACMZ2tMMZzQ8H9mWPHJcB7uYP47BM2zA")


if __name__ == '__main__':
    unittest.main()