import unittest
from bisq.asset.coins.zero_classic import ZeroClassic
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class ZeroClassicTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, ZeroClassic())

    def test_valid_addresses(self):
        self.assert_valid_address("t1PLfc14vCYaRz6Nv1zxpKXhn5W5h9vUdUE")
        self.assert_valid_address("t1MjXvaqL5X2CquP8hLmvyxCiJqCBzuMofS")

    def test_invalid_addresses(self):
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem")
        self.assert_invalid_address("38NwrYsD1HxQW5zfLT0QcUUXGMPvQgzTSn")
        self.assert_invalid_address("8tP9rh3SH6n9cSLmV22vnSNNw56LKGpLrB")
        self.assert_invalid_address("8Zbvjr")


if __name__ == "__main__":
    unittest.main()
