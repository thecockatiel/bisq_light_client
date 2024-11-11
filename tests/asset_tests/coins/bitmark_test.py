import unittest

from bisq.asset.coins.bitmark import Bitmark
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class BitmarkTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Bitmark())
    
    def test_valid_addresses(self):
        self.assert_valid_address("bMigVohTEiA3gxhFWpDJBrZ14j2RnDkWCs")
        self.assert_valid_address("bKMivcHXMNfs3P3AaTtyhDiZ7s8Nw3ek6L")
        self.assert_valid_address("bXUYGzbV8v6pLZtkYDL3feyrRFFnc37e3H")

    def test_invalid_addresses(self):
        self.assert_invalid_address("bMigVohTEiA3gxhFWpDJBrZ14j2RnDkWCt")
        self.assert_invalid_address("F9z7PKmo1sLQYtFuZjTQ1zZXhPQtHLScKT")
        self.assert_invalid_address("16Ftsh4Ff2ijPNsnQAUf5fKTp7DJaGxSZK")


if __name__ == '__main__':
    unittest.main()