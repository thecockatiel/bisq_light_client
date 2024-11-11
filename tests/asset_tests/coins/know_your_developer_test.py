import unittest

from bisq.asset.coins.know_your_developer import KnowYourDeveloper
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class KnowYourDeveloperTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, KnowYourDeveloper())
    
    def test_valid_addresses(self):
        self.assert_valid_address("Yezk3yX7A8sMsgiLN1DKBzhBNuosZLxyxv")
        self.assert_valid_address("YY9YLd5RzEVZZjkm2fsaWmQ2QP9aHcnCu9")
        self.assert_valid_address("YeJowNuWXx2ZVthswT5cLMQtMapfr7L9ch")

    def test_invalid_addresses(self):
        self.assert_invalid_address("yezk3yX7A8sMsgiLN1DKBzhBNuosZLxyxv")
        self.assert_invalid_address("yY9YLd5RzEVZZjkm2fsaWmQ2QP9aHcnCu9")
        self.assert_invalid_address("yeJowNuWXx2ZVthswT5cLMQtMapfr7L9ch")


if __name__ == '__main__':
    unittest.main()