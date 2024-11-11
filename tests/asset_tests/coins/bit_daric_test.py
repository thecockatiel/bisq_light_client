import unittest
from bisq.asset.coins.bit_daric import BitDaric
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class BitDaricTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, BitDaric())
    
    def test_valid_addresses(self):
        self.assert_valid_address("RKWuQUtmV3em1MyB7QKdshgDEAwKQXuifa")
        self.assert_valid_address("RG9YuDw7fa21a8h4E3Z2z2tgHrFNN27NnG")

    def test_invalid_addresses(self):
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem")
        self.assert_invalid_address("38NwrYsD1HxQW5zfLT0QcUUXGMPvQgzTSn")
        self.assert_invalid_address("8tP9rh3SH6n9cSLmV22vnSNNw56LKGpLrB")
        self.assert_invalid_address("8Zbvjr")


if __name__ == '__main__':
    unittest.main()