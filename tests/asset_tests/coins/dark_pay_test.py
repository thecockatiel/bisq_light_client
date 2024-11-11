import unittest
 
from bisq.asset.coins.dark_pay import DarkPay
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DarkPayTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, DarkPay())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("DXSi43hpVRjy1yGF3Vh3nnCK6ydwyWxVAD")
        self.assert_valid_address("DmHHAyocykozeW8fwJxPbn1o83dT4fDtoR")
        self.assert_valid_address("RSBxWDDMNxCKtnHvqf8Dsif5sm52ik36rW")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("DXSi43hpVRjy1yGF3Vh3nnCK6ydwyWxVAd")
        self.assert_invalid_address("DmHHAyocykozeW888888fwJxPbn1o83dT4fDtoR")
        self.assert_invalid_address("RSBxWDDMNxCKtnHvqf8Dsif5sm52ik35rW#")
        self.assert_invalid_address("3GyEtTwXhxbjBtmAR3CtzeayAyshtvd44P")
        self.assert_invalid_address("1CnXYrivw7pJy3asKftp41wRPgBggF9fBw")


if __name__ == '__main__':
    unittest.main()