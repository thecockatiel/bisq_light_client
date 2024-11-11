import unittest 
from bisq.asset.coins.counterparty import Counterparty
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CounterPartyTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Counterparty())
    
    def test_valid_addresses(self):
        self.assert_valid_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.assert_valid_address("1KBbojKRf1YnJKp1YK5eEz9TWlS4pFEbwS")
        self.assert_valid_address("1AtLN6BMlW0Rwj800LNcBBR2o0k0sYVuIN")    

    def test_invalid_addresses(self): 
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")
        self.assert_invalid_address("122FRU9f3fx7Hty641DRK6S3sbf3")
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")


if __name__ == '__main__':
    unittest.main()