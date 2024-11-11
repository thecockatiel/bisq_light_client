import unittest

from bisq.asset.coins.beam import Beam
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class BeamTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Beam())
    
    def test_valid_addresses(self):
        self.assert_valid_address("4a0e54b24d5fdf06891a8eaa57b4b3ac16731e932a64da8ec768083495d624f1")
        self.assert_valid_address("c7776e6d3fd3d9cc66f9e61b943e6d99473b16418ee93f3d5f6b70824cdb7f0a9")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("114a0e54b24d5fdf06891a8eaa57b4b3ac16731e932a64da8ec768083495d624f1111111111111111")


if __name__ == '__main__':
    unittest.main()