import unittest
from bisq.asset.coins.decred import Decred
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DecredTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Decred())
    
    def test_valid_addresses(self):
        self.assert_valid_address("Dcur2mcGjmENx4DhNqDctW5wJCVyT3Qeqkx")
        self.assert_valid_address("Dsur2mcGjmENx4DhNqDctW5wJCVyT3Qeqkx")
        self.assert_valid_address("Deur2mcGjmENx4DhNqDctW5wJCVyT3Qeqkx")    

    def test_invalid_addresses(self): 
        self.assert_invalid_address("aHu897ivzmeFuLNB6956X6gyGeVNHUBRgD")
        self.assert_invalid_address("a1HwTdCmQV3NspP2QqCGpehoFpi8NY4Zg3")
        self.assert_invalid_address("aHu897ivzmeFuLNB6956X6gyGeVNHUBRgD")


if __name__ == '__main__':
    unittest.main()