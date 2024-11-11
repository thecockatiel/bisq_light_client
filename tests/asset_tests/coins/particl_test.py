import unittest
from bisq.asset.coins.particl import Particl 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class ParticlCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Particl())
    
    def test_valid_addresses(self):
        self.assert_valid_address("PZdYWHgyhuG7NHVCzEkkx3dcLKurTpvmo6")
        self.assert_valid_address("RJAPhgckEgRGVPZa9WoGSWW24spskSfLTQ")
        self.assert_valid_address("PaqMewoBY4vufTkKeSy91su3CNwviGg4EK")
        self.assert_valid_address("PpWHwrkUKRYvbZbTic57YZ1zjmsV9X9Wu7")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhemqq")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYheO")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhek")


if __name__ == '__main__':
    unittest.main()