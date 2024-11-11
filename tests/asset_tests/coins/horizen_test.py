import unittest
 
from bisq.asset.coins.horizen import Horizen
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class HorizenTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Horizen())
    
    def test_valid_addresses(self):
        self.assert_valid_address("znk62Ey7ptTyHgYLaLDTEwhLF6uN1DXTBfa")
        self.assert_valid_address("znTqzi5rTXf6KJnX5tLaC5CMGHfeWJwy1c7")
        self.assert_valid_address("t1V9h2P9n4sYg629Xn4jVDPySJJxGmPb1HK")
        self.assert_valid_address("t3Ut4KUq2ZSMTPNE67pBU5LqYCi2q36KpXQ")

    def test_invalid_addresses(self):
        self.assert_invalid_address("zcKffBrza1cirFY47aKvXiV411NZMscf7zUY5bD1HwvkoQvKHgpxLYUHtMCLqBAeif1VwHmMjrMAKNrdCknCVqCzRNizHUq")
        self.assert_invalid_address("AFTqzi5rTXf6KJnX5tLaC5CMGHfeWJwy1c7")
        self.assert_invalid_address("zig-zag")
        self.assert_invalid_address("0123456789")


if __name__ == '__main__':
    unittest.main()