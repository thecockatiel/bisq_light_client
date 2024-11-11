import unittest
from bisq.asset.coins.litecoin import Litecoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class LitecoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Litecoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("Lg3PX8wRWmApFCoCMAsPF5P9dPHYQHEWKW")
        self.assert_valid_address("LTuoeY6RBHV3n3cfhXVVTbJbxzxnXs9ofm")
        self.assert_valid_address("LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW")
        self.assert_valid_address("ltc1qxtm55gultqzhqzl2p3ks50hg2478y3hehuj6dz")
        self.assert_valid_address("MGEW4aba3tnrVtVhGcmoqqHaLt5ymPSLPi")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("1LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW")
        self.assert_invalid_address("LgfapHEPhZbdRF9pMd5WPT35hFXcZS1USrW")
        self.assert_invalid_address("LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW#")
        self.assert_invalid_address("bc1qxtm55gultqzhqzl2p3ks50hg2478y3hehuj6dz")
        self.assert_invalid_address("MGEW4aba3tnrVtVhGcmoqqHaLt5ymPSLPW")


if __name__ == '__main__':
    unittest.main()