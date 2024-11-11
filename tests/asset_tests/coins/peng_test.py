import unittest
from bisq.asset.coins.peng import Peng
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class PengTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Peng())
    
    def test_valid_addresses(self):
        self.assert_valid_address("P9KqnVS9UpcJmLtCF1j4SV3fcccMuGEbhs")
        self.assert_valid_address("PUTXyY73s3HDvEzNJQekXMnjNjTrzFBzE2")
        self.assert_valid_address("PEfabj5DzRj6WBpc3jtVDorsVM5nddDxie")
        self.assert_valid_address("PAvXbSUAdCyd9MEtDPYYSmezmeLGL1HcjG")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("Pp9KqnVS9UpcJmLtCF1j4SV3fcccMuGEbhs")
        self.assert_invalid_address("PqUTXyY73s3HDvEzNJQekXMnjNjTrzFBzE2")
        self.assert_invalid_address("P8Efabj5DzRj6WBpc3jtVDorsVM5nddDxie")
        self.assert_invalid_address("P9AvXbSUAdCyd9MEtDPYYSmezmeLGL1HcjG")


if __name__ == '__main__':
    unittest.main()