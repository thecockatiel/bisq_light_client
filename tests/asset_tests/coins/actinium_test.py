import unittest

from bisq.asset.coins.actinium import Actinium
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CoinsTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Actinium())
    
    def test_valid_addresses(self):
        self.assert_valid_address("NLzB9iUGJ8GaKSn9GfVKfd55QVRdNdz9FK")
        self.assert_valid_address("NSz7PKmo1sLQYtFuZjTQ1zZXhPQtHLScKT")
        self.assert_valid_address("NTFtsh4Ff2ijPNsnQAUf5fKTp7DJaGxSZK")
        self.assert_valid_address("PLRiNpnTzWqufAoRFN1u9zBstHqjyM2qgB")
        self.assert_valid_address("PMFpWHR2AbBwaR4G2rA5nWB1F7cbZWua5Z")
        self.assert_valid_address("P9XE6tupGocWnsNgoUxRPzASYAPVAyu2T8")

    def test_invalid_addresses(self):
        self.assert_invalid_address("MgTFtsh4Ff2ijPNsnQAUf5fKTp7DJaGxSZK")
        self.assert_invalid_address("F9z7PKmo1sLQYtFuZjTQ1zZXhPQtHLScKT")
        self.assert_invalid_address("16Ftsh4Ff2ijPNsnQAUf5fKTp7DJaGxSZK")
        self.assert_invalid_address("Z6Ftsh7LfGijPVzmQAUf5fKTp7DJaGxSZK")
        self.assert_invalid_address("G5Fmxy4Ff2ijLjsnQAUf5fKTp7DJaGxACV")
        self.assert_invalid_address("D4Hmqy4Ff2ijXYsnQAUf5fKTp7DJaGxBhJ")


if __name__ == '__main__':
    unittest.main()