import unittest

from bisq.asset.coins.navcoin import Navcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class NavcoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Navcoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("NNR93HzmuhYKZ4Tnc9TGoD2DK6TVzXG9P7")
        self.assert_valid_address("NSm5NyCe5BFRuV3gFY5VcfhxWx7GTu9U9F")
        self.assert_valid_address("NaSdzJ64o8DQo5DMPexVrL4PYFCBZqcmsW")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("NNR93HzmuhYKZ4Tnc9TGoD2DK6TVzXG9P")
        self.assert_invalid_address("NNR93HzmuhYKZ4TnO9TGoD2DK6TVzXG9P8")
        self.assert_invalid_address("NNR93HzmuhYKZ4Tnc9TGoD2DK6TVzXG9P71")


if __name__ == '__main__':
    unittest.main()