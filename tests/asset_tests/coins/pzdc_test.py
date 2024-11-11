import unittest
from bisq.asset.coins.pzdc import PZDC
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class PZDCTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, PZDC())
    
    def test_valid_addresses(self):
        self.assert_valid_address("PNxERPUbkvCYeuJk44pH8bsdQJenvEWt5J")
        self.assert_valid_address("PCwCT1PkW2RsxT8jTb21vRnNDQGDRcWNkM")
        self.assert_valid_address("PPD3mYyS3vsHBkCrbCfrZyrwCGdr6EJHgG")
        self.assert_valid_address("PTQDhqksrocR7Z516zbpjuXSGVD37iu8gy")
        self.assert_valid_address("PXtABooQW1ED9NkARTiFcZv6xUnMmrbhpt")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("pGXsg0jSMzh1dSqggRvHjPvE3cnwvuXC7s")
        self.assert_invalid_address("PKfRRcjwzKFq3dIqE9gq8Ztxn922W4GZhm")
        self.assert_invalid_address("PKfRRcjwzKFq3d0qE9gq8Ztxn922W4GZhm")
        self.assert_invalid_address("PKfRRcjwzKFq3dOqE9gq8Ztxn922W4GZhm")
        self.assert_invalid_address("PKfRRcjwzKFq3dlqE9gq8Ztxn922W4GZhm")
        self.assert_invalid_address("PXP75NnwDryYswQb9RaPFBchqLRSvBmDP")
        self.assert_invalid_address("PKr3vQ7S")


if __name__ == '__main__':
    unittest.main()