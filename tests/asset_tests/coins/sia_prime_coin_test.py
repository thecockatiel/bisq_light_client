import unittest
from bisq.asset.coins.sia_prime_coin import SiaPrimeCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class SiaPrimeCoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, SiaPrimeCoin())

    def test_valid_addresses(self):
        self.assert_valid_address("d9fe1331ed2ae1bbdfe0e2942e84d74b7310648e5a5f14c4980ec2c6a19f08af6894b9060e83")
        self.assert_valid_address("205cf3be0f04397ee6cc1f52d8ae47f589a4ef5936949c158b2555df291efb87db2bbbca2031")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("205cf3be0f04397ee6cc1f52d8ae47f589a4ef5936949c158b2555df291efb87db2bbbca20311")
        self.assert_invalid_address("205cf3be0f04397ee6cc1f52d8ae47f589a4ef5936949c158b2555df291efb87db2bbbca203")
        self.assert_invalid_address("205cf3be0f04397ee6cc1f52d8ae47f589a4ef5936949c158b2555df291efb87db2bbbca2031#")
        self.assert_invalid_address("bvQpKvb1SswwxVTuyZocHWCVsUeGq7MwoR")
        self.assert_invalid_address("d9fe1331ed2ae1bbdfe0e2942e84d74b7310648e5a5f14c4980ec2c6a19f08af6894b9060E83")

if __name__ == "__main__":
    unittest.main()
