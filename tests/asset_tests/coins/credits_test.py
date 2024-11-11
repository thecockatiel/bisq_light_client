import unittest

from bisq.asset.coins.credits import Credits
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CreditsTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Credits())
    
    def test_valid_addresses(self):
        self.assert_valid_address("CfXBhPhSxx1wqxGQCryfgn6iU1M1XFUuCo")
        self.assert_valid_address("CMde7YERCFWkCL2W5i8uyJmnpCVj8Chhww")
        self.assert_valid_address("CcbqU3MLZuGAED2CuhUkquyJxKaSJqv6Vb")
        self.assert_valid_address("CKaig5pznaUgiLqe6WkoCNGagNMhNLtqhK")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1fXBhPhSxx1wqxGQCryfgn6iU1M1XFUuCo32")
        self.assert_invalid_address("CMde7YERCFWkCL2W5i8uyJmnpCVj8Chh")
        self.assert_invalid_address("CcbqU3MLZuGAED2CuhUkquyJxKaSJqv6V6#")
        self.assert_invalid_address("bKaig5pznaUgiLqe6WkoCNGagNMhNLtqhKkggg")


if __name__ == '__main__':
    unittest.main()