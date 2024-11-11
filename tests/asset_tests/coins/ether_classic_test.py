import unittest

from bisq.asset.coins.ether_classic import EtherClassic
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class EtherClassicTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, EtherClassic())
    
    def test_valid_addresses(self):
        self.assert_valid_address("0x353c13b940aa5eed75aa97d477954289e7880bb8")
        self.assert_valid_address("0x9f5304DA62A5408416Ea58A17a92611019bD5ce3")
        self.assert_valid_address("0x180826b05452ce96E157F0708c43381Fee64a6B8")

    def test_invalid_addresses(self):
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")
        self.assert_invalid_address("N22FRU9f3fx7Hty641D5cg95kRK6S3sbf3")
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")


if __name__ == '__main__':
    unittest.main()