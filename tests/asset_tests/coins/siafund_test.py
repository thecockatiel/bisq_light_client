import unittest
from bisq.asset.coins.siafund import Siafund
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class SiafundTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Siafund())

    def test_valid_addresses(self):
        self.assert_valid_address("949f35966a9b5f329f7419f91a02301b71b9f776568b2c767842af22b408eb8662203a02ec53")
        self.assert_valid_address("4daae3005456559972f4902217ee8394a890e2afede6f0b49015e5cfaecdcb13f466f5543346")
        self.assert_valid_address("da4f7fdc0fa047851a9860b09bc9b1e7424333c977e53a5d8aad74f5843a20b7cfa77a7794ae")        

    def test_invalid_addresses(self):
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")
        self.assert_invalid_address("N22FRU9f3fx7Hty641D5cg95kRK6S3sbf3")
        self.assert_invalid_address("MxmFPEPzF19JFPU3VPrRXvUbPjMQXnQerY")        

if __name__ == "__main__":
    unittest.main()
