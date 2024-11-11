import unittest
from bisq.asset.coins.qm_coin import QMCoin 
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class QMCoinTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, QMCoin())
    
    def test_valid_addresses(self):
        self.assert_valid_address("QSXwS2opau1PYsvj4PrirPkP6LQHeKbQDx")
        self.assert_valid_address("QbvD8CPJwAmpQoE8CQhzcfWp1EAmT2E298")
        self.assert_valid_address("QUAzsb7nqp7XVsRy9vjaE4kTUpgP1pFeoL")
        self.assert_valid_address("QQDvVM2s3WYa8EZQS1s2esRkR4zmrjy94d")
        self.assert_valid_address("QgdkWtsy1inr9j8RUrqDeVnrJmhE28WnLX")
        self.assert_valid_address("Qii56aanBMiEPpjHoaE4zgEW4jPuhGjuj5")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("qSXwS2opau1PYsvj4PrirPkP6LQHeKbQDx")
        self.assert_invalid_address("QbvD8CPJwAmpQoE8CQhzcfWp1EAmT2E2989")
        self.assert_invalid_address("QUAzsb7nq07XVsRy9vjaE4kTUpgP1pFeoL")
        self.assert_invalid_address("QQDvVM2s3WYa8EZQS1s2OsRkR4zmrjy94d")
        self.assert_invalid_address("QgdkWtsy1inr9j8RUrqDIVnrJmhE28WnLX")
        self.assert_invalid_address("Qii56aanBMiEPpjHoaE4lgEW4jPuhGjuj5")


if __name__ == '__main__':
    unittest.main()