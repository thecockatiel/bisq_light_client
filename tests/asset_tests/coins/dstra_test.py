import unittest

from bisq.asset.coins.dstra import DSTRA
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DSTRATest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, DSTRA())
    
    def test_valid_addresses(self):
        self.assert_valid_address("DGiwGS8n3tJZuKxUdWF6MyTYvv6xgDcyd7")
        self.assert_valid_address("DQcAKx5bFoeRwAEHE4EHQykyq8u2M1pwFa")

    def test_invalid_addresses(self):
        self.assert_invalid_address("DGiwGS8n3tJZuKxUdWF6MyTYvv6xgDcyd77")
        self.assert_invalid_address("DGiwGS8n3tJZuKxUdWF6MyTYvv6xgDcyd")
        self.assert_invalid_address("dGiwGS8n3tJZuKxUdWF6MyTYvv6xgDcyd7")
        self.assert_invalid_address("FGiwGS8n3tJZuKxUdWF6MyTYvv6xgDcyd7")
        self.assert_invalid_address("fGiwGS8n3tJZuKxUdWF6MyTYvv6xgDcyd7")


if __name__ == '__main__':
    unittest.main()