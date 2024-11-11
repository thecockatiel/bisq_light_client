import unittest
from bisq.asset.coins.spectrecoin import Spectrecoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class SpectrecoinTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Spectrecoin())

    def test_valid_addresses(self):
        self.assert_valid_address("SUZRHjTLSCr581qLsGqMqBD5f3oW2JHckn")
        self.assert_valid_address("SZ4S1oFfUa4a9s9Kg8bNRywucHiDZmcUuz")
        self.assert_valid_address("SdyjGEmgroK2vxBhkHE1MBUVRbUWpRAdVG")

    def test_invalid_addresses(self):
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhemqq")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYheO")
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhek")

if __name__ == "__main__":
    unittest.main()
