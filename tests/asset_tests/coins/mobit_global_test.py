import unittest 
from bisq.asset.coins.mobit_global import MobitGlobal
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MobitGlobalTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, MobitGlobal())

    def test_valid_addresses(self):
        self.assert_valid_address("MKDLXTdJs1AtAJhoRddLBSimXCE6SXbyMq")
        self.assert_valid_address("MGr2WYY9kSLPozEcsCWSEumXNX2AJXggUR")
        self.assert_valid_address("MUe1HzGqzcunR1wUxHTqX9cuQNMnEjiN7D")
        self.assert_valid_address("MWRqbYKkQcSvtHq4GFrPvYGf8GFGsLNPcE")

    def test_invalid_addresses(self):
        self.assert_invalid_address("AWGfbG22DNhgP2rsKfqyFxCwi1u68BbHAA1")
        self.assert_invalid_address("AWGfbG22DNhgP2rsKfqyFxCwi1u68BbHAB")
        self.assert_invalid_address("AWGfbG22DNhgP2rsKfqyFxCwi1u68BbHA#")

if __name__ == "__main__":
    unittest.main()
