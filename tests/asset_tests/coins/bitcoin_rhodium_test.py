import unittest

from bisq.asset.coins.bitcoin_rhodium import BitcoinRhodium
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class ActeniumTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, BitcoinRhodium())

    def test_valid_addresses(self):
        self.assert_valid_address("RiMBe4uDXPzTxgKUEwqQobp2o7dqBDYM6S")
        self.assert_valid_address("RqvpFWRTSKo2QEMH89rNhs3C7CCmRRYKmg")
        self.assert_valid_address("Rhxz2uF9HaE2ync4eDetjkdhkS5qMXMQzz")

    def test_invalid_addresses(self):
        self.assert_invalid_address("Rhxz2uF9HaE2ync4eDetjkdhkS5qMXMQvdvdfbFzz")
        self.assert_invalid_address("fqvpFWRTSKo2QEMH89rNhs3C7CCmRRYKmg")
        self.assert_invalid_address("1HQQgsvLTgN9xD9hNmAgAreakzDsxUSLSH#")


if __name__ == "__main__":
    unittest.main()
