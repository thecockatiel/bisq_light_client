import unittest
from bisq.asset.coins.qbase import Qbase 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class QbaseTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Qbase())
    
    def test_valid_addresses(self):
        self.assert_valid_address("BBrv1uUkQxpWayMvaVSw9Gr4X7CcdWUtcC")
        self.assert_valid_address("BNMFjkDk9qqcF2rtoAbqbqWiHa41GPkQ2G")
        self.assert_valid_address("B73WdFQXx8VGNg8h1BeJj6H2BEa1xrbtsT")
        self.assert_valid_address("BGq4DH2BnS4kFWuNNQqfmiDLZvjaWtvnWX")
        self.assert_valid_address("B9b8iTbVVcQrohrEnJ9ho4QUftHS3svB84")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("bBrv1uUkQxpWayMvaVSw9Gr4X7CcdWUtcC")
        self.assert_invalid_address("B3rv1uUkQxpWayMvaVSw9Gr4X7CcdWUtcC")
        self.assert_invalid_address("PXP75NnwDryYswQb9RaPFBchqLRSvBmDP")
        self.assert_invalid_address("PKr3vQ7S")


if __name__ == '__main__':
    unittest.main()