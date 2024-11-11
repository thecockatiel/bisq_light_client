import unittest
from bisq.asset.coins.webchain import Webchain
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class WebchainTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Webchain())

    def test_valid_addresses(self):
        self.assert_valid_address("0x8d1ba0497c3e3db17143604ab7f5e93a3cbac68b")
        self.assert_valid_address("0x23c9c5ae8c854e9634a610af82924a5366a360a3")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("8d1ba0497c3e3db17143604ab7f5e93a3cbac68b")
        self.assert_invalid_address("0x8d1ba0497c3e3db17143604ab7f5e93a3cbac68")
        self.assert_invalid_address("0x8d1ba0497c3e3db17143604ab7f5e93a3cbac68k")
        self.assert_invalid_address("098d1ba0497c3e3db17143604ab7f5e93a3cbac68b")
        self.assert_invalid_address("098d1ba0497c3e3db17143604ab7f5e93a3cbac68b")


if __name__ == "__main__":
    unittest.main()
