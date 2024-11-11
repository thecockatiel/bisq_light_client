import unittest

from bisq.asset.coins.kekcoin import Kekcoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class KekcoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Kekcoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("KHWHFVU5ZMUfkiYEMMuXRDv1LjD2j1HJ2H")
        self.assert_valid_address("KSXQWsaKC9qL2e2RoeXNXY4FgQC6qUBpjD")
        self.assert_valid_address("KNVy3X1iuiF7Gz9a4fSYLF3RehN2yGkFvP")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW")
        self.assert_invalid_address("1K5B7SDcuZvd2oUTaW9d62gwqsZkteXqA4")
        self.assert_invalid_address("1GckU1XSCknLBcTGnayBVRjNsDjxqopNav")


if __name__ == '__main__':
    unittest.main()