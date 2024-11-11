import unittest

from bisq.asset.coins.namecoin import Namecoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class NamecoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Namecoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("N7yhcPhzFduWXPc11AUK9zvtnsL6sgxmRs")
        self.assert_valid_address("N22FRU9f3fx7Hty641D5cg95kRK6S3sbf3")
        self.assert_valid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("N7yhcPhzFduWXPc11AUK9zvtnsL6sgxmRsx")
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQer")
        self.assert_invalid_address("bc1qus65zpte6qa2408qu3540lfcyj9cx7dphfcspn")
        self.assert_invalid_address("3GyEtTwXhxbjBtmAR3CtzeayAyshtvd44P")
        self.assert_invalid_address("1CnXYrivw7pJy3asKftp41wRPgBggF9fBw")


if __name__ == '__main__':
    unittest.main()