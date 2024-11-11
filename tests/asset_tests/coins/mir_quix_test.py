import unittest
from bisq.asset.coins.mir_quix import MirQuiX
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MirQuiXTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, MirQuiX())

    def test_valid_addresses(self): 
        self.assert_valid_address("MCfFP5bFtN9riJiRRnH2QRkqCDqgNVC3FX")
        self.assert_valid_address("MEoLjNvFbNv63NtBW6eyYHUAGgLsJrpJbG")
        self.assert_valid_address("M84gmHb7mg4PMNBpVt3BeeAWVuKBmH6vtd")
        self.assert_valid_address("MNurUTgTSgg5ckmCcbjPrkgp7fekouLYgh")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("MCfFP5bFtN9riJiRRnH2QRkqCDqgNVC3FX2")
        self.assert_invalid_address("MmEoLjNvFbNv63NtBW6eyYHUAGgLsJrpJbG")
        self.assert_invalid_address("M84gmHb7mg4PMNBpVt3BeeAWVuKBmH63vtd")
        self.assert_invalid_address("MNurUTgTSgg5ckmCcbjPrkgp7fekouLYfgh")

if __name__ == "__main__":
    unittest.main()
