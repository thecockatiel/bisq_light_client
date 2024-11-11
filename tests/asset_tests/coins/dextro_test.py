import unittest

from bisq.asset.coins.dextro import Dextro
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DextroTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Dextro())
    
    def test_valid_addresses(self):
        self.assert_valid_address("DP9LSAMzxNAuSei1GH3pppMjDqBhNrSGov")
        self.assert_valid_address("D8HwxDXPJhrSYonPF7YbCGENkM88cAYKb5")
        self.assert_valid_address("DLhJt6UfwMtWLGMH3ADzjqaLaGG6Bz96Bz")

    def test_invalid_addresses(self):
        self.assert_invalid_address("DP9LSAMzxNAuSei1GH3pppMjDqBhNrSG0v")
        self.assert_invalid_address("DP9LSAMzxNAuSei1GH3pppMjDqBhNrSGovx")
        self.assert_invalid_address("DP9LSAMzxNAuSei1GH3pppMjDqBhNrSG#v")


if __name__ == '__main__':
    unittest.main()