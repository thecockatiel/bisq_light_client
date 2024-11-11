import unittest
from bisq.asset.coins.cloak_coin import CloakCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CloakCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, CloakCoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("C3MwbThsvquwA4Yg6recThXpAhR2hvRKws")
        self.assert_valid_address("B6MwbThsvquwA4Yg6recThXpAhR2hvKRsz")
        self.assert_valid_address("BCA31xPpijxiCuTQeYMpMTQsTH1m2jTg5t")
        self.assert_valid_address("smYmLVV33zExmaFyVp3AUjU3fJMK5E93kwzDfMnPLnEBQ7BoHZkSQhCP92hZz7Hm24yavCceNeQm8RHekqdvrhFe8gX7EdXNwnhQgQ")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1sA31xPpijxiCuTQeYMpMTQsTH1m2jTgtS")
        self.assert_invalid_address("BsA31xPpijxiCuTQeYMpMTQsTH1m2jTgtSd")
        self.assert_invalid_address("bech3ThsvquwA4Yg6recThXpAhR2hvRKws")
        self.assert_invalid_address("smYmLYcVVzExmaFyVp3AUjU3fJMK5E93kwzDfMnPLnEBQ7BoHZkSQhCP92hZz7Hm24yavCceNeQm8RHekqdv")
        self.assert_invalid_address("C3MwbThsvquwA4Yg6recThXpAhR2hvRKw")
        self.assert_invalid_address(" B6MwbThsvquwA4Yg6recThXpAhR2hvKRsz")
        self.assert_invalid_address("B6MwbThsvquwA4Yg6recThXpAhR2hvKRsz ")


if __name__ == '__main__':
    unittest.main()