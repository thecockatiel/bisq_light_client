import unittest
 
from bisq.asset.coins.genesis import Genesis
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class GenesisTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Genesis())
    
    def test_valid_addresses(self):
        self.assert_valid_address("STE5agX1VkUKZRTHBFufkQu6JtNP1QYJcd") # Standard SegWit
        self.assert_valid_address("SNMcFfcFkes6bWR5dviWQQAL4SYQg8T4Vu") # Standard SegWit
        self.assert_valid_address("SfMmJJdg8uDHK6ajurBNksry7zu3KHdbPv") # Standard SegWit

    def test_invalid_addresses(self):
        self.assert_invalid_address("genx1q5dlyjsktuztnwzs85as7vslqfddcmenhfc0ehl") # Bech32
        self.assert_invalid_address("genx1qxc0hp76tx9hse2evt8dx2k686nx42ljel5nenr") # Bech32
        self.assert_invalid_address("CT747k1CThgCxk4xRPQeJP6pyKiTfzRM1R") # valid but unsupported legacy
        self.assert_invalid_address("CbGwkAWfLXjU2esjomFzJfKAFdUiKQjJUd") # valid but unsupported legacy
        self.assert_invalid_address("0213ba949e295aabda252662ffed7c4c0906") # random garbage
        self.assert_invalid_address("BwyzAAjVwV2mhR2WQ8SfXhHyUDoy4VL16zBc") # random garbage
        self.assert_invalid_address("EpGQR83U34JRszcGENjegZLCoDLTwG6YWLBN7jVC") # random garbage
        self.assert_invalid_address("Xp3Gv2JiP487Z8SULctveCKNM1ffpz5b3n") # random garbage


if __name__ == '__main__':
    unittest.main()