import unittest

from bisq.asset.coins.chaucha import Chaucha
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class ChauchaTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Chaucha())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("cTC7AodMWM4fXsG1TDu4JLn2qKQoMg4F9N")
        self.assert_valid_address("caWnffHrx8wkQqcSVJ7wpRvN1E7Ztz7kPP")
        self.assert_valid_address("ciWwaG4trw1vQZSL4F4phQqznK4NgZURdQ")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1cTC7AodMWM4fXsG1TDu4JLn2qKQoMg4F9N")
        self.assert_invalid_address("cTC7AodMWM4fXsG1TDu4JLn2qKQoMg4F9XN")
        self.assert_invalid_address("cTC7AodMWM4fXsG1TDu4JLn2qKQoMg4F9N#")


if __name__ == '__main__':
    unittest.main()