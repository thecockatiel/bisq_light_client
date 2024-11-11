import unittest

from bisq.asset.coins.helium import Helium
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class HeliumTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Helium())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("SPSXRJSwzGKxSiYXePf1vnkk4v9WKVLhZp")
        self.assert_valid_address("SbzXDLmMfWDJZ1wEikUVAMbAzM2UnaSt4g")
        self.assert_valid_address("Sd14293Zhxxur2Pim7NkjxPGVaJTjGR5qY")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("1PSXRJSwzGKxSiYXePf1vnkk4v9WKVLhZp")
        self.assert_invalid_address("SPSXRJSwzGKxSiYXePf1vnkk4v9WKVLhZpp")
        self.assert_invalid_address("SPSSPSSPSGKxSiYXePf1vnkk4v9WKVLhZp#")


if __name__ == '__main__':
    unittest.main()