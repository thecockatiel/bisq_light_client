import unittest
from bisq.asset.coins.starwels import Starwels
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class StarwelsTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Starwels())

    def test_valid_addresses(self):
        self.assert_valid_address("1F7EixuiBdvi9bVxEPzAgJ11GRJsdH3ihh")
        self.assert_valid_address("17DdVnWvz3XZPvMYHmSRSycUgt2EEv29So")
        self.assert_valid_address("1HuoFLoGJQCLodNDH5oCXWaR1kL8DwksJX")

    def test_invalid_addresses(self):
        self.assert_invalid_address("21HQQgsvLTgN9xD9hNmAgAreakzVzQUSLSHa")
        self.assert_invalid_address("1HQQgsvLTgN9xD9hNmAgAreakzVzQUSLSHs")
        self.assert_invalid_address("1HQQgsvLTgN9xD9hNmAgAreakzVzQUSLSH#")

if __name__ == "__main__":
    unittest.main()
