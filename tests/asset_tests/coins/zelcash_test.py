import unittest
from bisq.asset.coins.zel_cash import ZelCash
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class ZelCashTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, ZelCash())

    def test_valid_addresses(self):
        self.assert_valid_address("t1K6LGT7z2uNTLxag6eK6XwGNpdkHbncBaK")
        self.assert_valid_address("t1ZjdqCGEkqL9nZ8fk9R6KA7bqNvXaVLUpF")

    def test_invalid_addresses(self):
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem")
        self.assert_invalid_address("38NwrYsD1HxQW5zfLT0QcUUXGMPvQgzTSn")
        self.assert_invalid_address("8tP9rh3SH6n9cSLmV22vnSNNw56LKGpLrB")
        self.assert_invalid_address("8Zbvjr")


if __name__ == "__main__":
    unittest.main()
