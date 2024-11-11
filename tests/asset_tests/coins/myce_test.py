import unittest
from bisq.asset.coins.myce import Myce
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MyceTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Myce())

    def test_valid_addresses(self):
        self.assert_valid_address("MCgtattGUWUBAV8n2JAa4uDWCRvbZeVcaD")
        self.assert_valid_address("MRV2dtuxwo8b1JSkwBXN3uGypJxp85Hbqn")
        self.assert_valid_address("MEUvfCySnAqzuNvbRh2SZCbSro8e2dxLYK")

    def test_invalid_addresses(self):
        self.assert_invalid_address("MCgtattGUWUBAV8n2JAa4uDWCRvbZeVcaDx")
        self.assert_invalid_address("AUV2dtuxwo8b1JSkwBXN3uGypJxp85Hbqn")
        self.assert_invalid_address("SEUvfCySnAqzuNvbRh2SZCbSro8e2dxLYK")

if __name__ == "__main__":
    unittest.main()
