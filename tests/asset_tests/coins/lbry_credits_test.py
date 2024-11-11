import unittest
from bisq.asset.coins.lbry_credits import LBRYCredits
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class LBRYCreditsTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, LBRYCredits())
    
    def test_valid_addresses(self):
        self.assert_valid_address("bYqg2q19uWmp3waRwptzj6o8e9viHgcA9z")
        self.assert_valid_address("bZEnLbYb3D29Sbo8QJdiQ2PQ3En6em31gt")
        self.assert_valid_address("rQ26jd9mqdfPizHZUdyMjUPgK6rRANPjne")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("")
        self.assert_invalid_address("Don'tBeSilly")
        self.assert_invalid_address("_rQ26jd9mqdfPizHZUdyMjUPgK6rRANPjne")
        self.assert_invalid_address("mzYvN2WuVLyp6RZE94rzzvZwBDfCdCse6i")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem")
        self.assert_invalid_address("3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX")
        self.assert_invalid_address("bYqg2q19uWmp3waRwptzj6o8e9viHgcA9a")
        self.assert_invalid_address("bYqg2q19uWmp3waRwptzj6o8e9viHgcA9za")


if __name__ == '__main__':
    unittest.main()