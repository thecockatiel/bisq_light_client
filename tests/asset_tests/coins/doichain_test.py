import unittest

from bisq.asset.coins.doichain import Doichain
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DoichainTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Doichain())
    
    def test_valid_addresses(self):
        self.assert_valid_address("NGHV9LstnZfrkGx5QJmYhEepbzc66W7LN5")
        self.assert_valid_address("N4jeY9YhU49qHN5wUv7HBxeVZrFg32XFy7")
        self.assert_valid_address("6a6xk7Ff6XbgrNWhSwn7nM394KZJNt7JuV")

    def test_invalid_addresses(self):
        self.assert_invalid_address("NGHV9LstnZfrkGx5QJmYhEepbzc66W7LN5x")
        self.assert_invalid_address("16iWWt1uoG8Dct56Cq6eKHFxvGSDha46Lo")
        self.assert_invalid_address("38BFQkc9CdyJUxQK8PhebnDcA1tRRwLDW4")


if __name__ == '__main__':
    unittest.main()