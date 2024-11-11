import unittest

from bisq.asset.coins.emercoin import Emercoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class EmercoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Emercoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("EedXjU95QcVHLEFAs5EKNT9UWqAWXTyuhD") # Regular p2pkh address
        self.assert_valid_address("EHNiED27Un5yKHHsGFDsQipCH4TdsTo5xb") # Regular p2pkh address
        self.assert_valid_address("eMERCoinFunera1AddressXXXXXXYDAYke") # dummy p2pkh address

    def test_invalid_addresses(self):
        self.assert_invalid_address("19rem1SSWTphjsFLmcNEAvnfHaBFuDMMae") # Valid BTC
        self.assert_invalid_address("EedXjU95QcVHLEFAs5EKNT9UWqAWXTyuhE") # Invalid EMC address
        self.assert_invalid_address("DDWUYQ3GfMDj8hkx8cbnAMYkTzzAunAQxg") # Valid DOGE


if __name__ == '__main__':
    unittest.main()