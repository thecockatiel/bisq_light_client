import unittest
 
from bisq.asset.coins.burnt_black_coin import BurntBlackCoin
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class BurntBlackCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, BurntBlackCoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("4b")
        self.assert_valid_address("536865206d616b657320796f75206275726e207769746820612077617665206f66206865722068616e64")
        long_address = 'af' * (2 * BurntBlackCoin.PAYLOAD_LIMIT)
        self.assert_valid_address(long_address)

    def test_invalid_addresses(self):
        self.assert_invalid_address("AF")
        self.assert_invalid_address("afa")
        self.assert_invalid_address("B4Wa1C8zFgkSY4daLg8jWnxuKpw7UmWFoo")
        too_long_address = 'af' * (2 * BurntBlackCoin.PAYLOAD_LIMIT + 1)
        self.assert_invalid_address(too_long_address)


if __name__ == '__main__':
    unittest.main()