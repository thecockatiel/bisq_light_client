import unittest
 
from bisq.asset.coins.gamble_coin import GambleCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class GambleCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, GambleCoin())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("CKWCoP2Cog4gU3ARzNqGEqwDxNZNVEpPJP")
        self.assert_valid_address("CJmvkF84bW93o5E7RFe4VzWMSt4WcKo1nv")
        self.assert_valid_address("Caz2He7kZ8ir52CgAmQywCjm5hRjo3gLwT")
        self.assert_valid_address("CM2fRpzpxqyRvaWxtptEmRzpGCFE1qCA3V")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("CKWCoP2C0g4gU3ARzNqGEqwDxNZNVEpPJP")
        self.assert_invalid_address("CJmvkF84bW93o5E7RFe4VzWMSt4WcKo1nvx")
        self.assert_invalid_address("Caz2He7kZ8ir52CgAmQywC#m5hRjo3gLwT")
        self.assert_invalid_address("DM2fRpzpxqyRvaWxtptEmRzpGCFE1qCA3V")


if __name__ == '__main__':
    unittest.main()