import unittest 
from bisq.asset.coins.ida_pay import IdaPay
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class IdaPayTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, IdaPay())
    
    def test_valid_addresses(self):  
        self.assert_valid_address("Cj6A8JJvovgSTiMc4r6PaJPrfwQnwnHDpg")
        self.assert_valid_address("D4SEkXMAcxRBu2Gc1KpgcGunAu5rWttjRy")
        self.assert_valid_address("CopBThXxkziyQEG6WxEfx36Ty46DygzHTW")
        self.assert_valid_address("D3bEgYWDS7fxfu9y1zTSrcdP681w3MKw6W")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("Cj6A8JJv0vgSTiMc4r6PaJPrfwQnwnHDpg")
        self.assert_invalid_address("D4SEkXMAcxxRBu2Gc1KpgcGunAu5rWttjRy")
        self.assert_invalid_address("CopBThXxkziyQEG6WxEfx36Ty4#DygzHTW")
        self.assert_invalid_address("13bEgYWDS7fxfu9y1zTSrcdP681w3MKw6W")


if __name__ == '__main__':
    unittest.main()