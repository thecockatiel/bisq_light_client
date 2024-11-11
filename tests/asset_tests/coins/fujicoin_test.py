import unittest

from bisq.asset.coins.fujicoin import Fujicoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class FujicoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Fujicoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("FpEbvwxhmer2zSvqh61JtLiffu8Tk2abdo")
        self.assert_valid_address("7gcLWi78MFJ9akMzTAiug3uArvPch5LB6q")
        self.assert_valid_address("FrjN1LLWJj1DWVooBCdybBvmaEAqxMuuq8")

    def test_invalid_addresses(self):
        self.assert_invalid_address("MgTFtsh4Ff2ijPNsnQAUf5fKTp7DJaGxSZK")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem")
        self.assert_invalid_address("FpEbvwxhmer2zSvqh61JtLiffu8Tk2abda")
        self.assert_invalid_address("7gcLWi78MFJ9akMzTAiug3uArvPch5LB6a")
        self.assert_invalid_address("fc1q3s2fc2xqgush29urtfdj0vhcj96h8424zyl6wa")


if __name__ == '__main__':
    unittest.main()