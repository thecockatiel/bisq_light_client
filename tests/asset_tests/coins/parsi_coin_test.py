import unittest
from bisq.asset.coins.parsi_coin import ParsiCoin 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class ParsiCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, ParsiCoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("PARSGnjdcRG4gY9g4rMTFAEHZLGU7uK8YMiFY3Do1uzoMz4LMA6PqmdPp7ZxDu25b56RyhCevkWjbAMng532iFFj8L5RaPyT4s")
        self.assert_valid_address("PARSftfY5pwJaUFtaxThVgKY9Sepd4mG44WpyncbtAxTddwTvJ84GCgGfoxYjzG53kLhRm21ENWp3fx5bneArq1D815ZoWNVqA")
        self.assert_valid_address("PARSju1hCQ5GmXSRbca8weGYDn2pqCypgLyTrENqL4XU3mdEx1mZ2vR7osrVA2hHNGRJRA5pRENF2Q8Pee8BscHoABVrcfkWnx")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("")
        self.assert_invalid_address("1GfqxEuuFmwwHTFkch3Aq3frEBbdpYfWPP")
        self.assert_invalid_address("PARsaUEu1c9HWPQx6WpCcjZNmpS3vMhN4Jws12KrccLhH9vzUw4racG3g7St2FKDYngjcnkNF3N2sKQJ5jv1NYqD2buCpmVKE")
        self.assert_invalid_address("PArSeoCiQL2Rjyo9GR39boeLCTM6ou3zGiv8AuFFblGHfNasy5iKfvG6JgnksNby26J6i5sEorRcmG8gF2AxC8bYiHyDGEfD6hp8T9KfwjQxVa")
        self.assert_invalid_address("PaRSaUEu1c9HWPQx6WpCcjZNmpS3vMhN4Jws12rccLhH9vzUw4racG3g7St2#FKDYngjcnkNF3N2sKQJ5jv1NYqD2buCpmVKE")
        self.assert_invalid_address("pARSeoCiQL2Rjyo9GR39boeLCTM6ou3zGiv8AuFFby5iKfvG6JNby26J6i5s$&*orRcmG8gF2AxC8bYiHyDGEfD6hp8T9KfwjQxVa")
        self.assert_invalid_address("hyrjMmPhaznQkJD6C9dcmbBH9y6r9vYAg2aTG9CHSzL1R89xrFi7wj1azmkXyLPiWDBeTCsKGMmr6JzygbP2ZGSN2JqWs1WcK")
        self.assert_invalid_address("parsGnjdcRG4gY9g4rMTFAEHZLGU7uK8YMiFY3Do1uzoMz4LMA6PqmdPp7ZxDu25b56RyhCevkWjbAMng532iFFj8L5RaPyT")


if __name__ == '__main__':
    unittest.main()