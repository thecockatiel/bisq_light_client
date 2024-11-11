import unittest
from bisq.asset.coins.pivx import PIVX
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class PIVXTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, PIVX())
    
    def test_valid_addresses(self):
        self.assert_valid_address("DFJku78A14HYwPSzC5PtUmda7jMr5pbD2B")
        self.assert_valid_address("DAeiBSH4nudXgoxS4kY6uhTPobc7ALrWDA")
        self.assert_valid_address("DRbnCYbuMXdKU4y8dya9EnocL47gFjErWe")
        self.assert_valid_address("DTPAqTryNRCE2FgsxzohTtJXfCBCDnG6Rc")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("dFJku78A14HYwPSzC5PtUmda7jMr5pbD2B")
        self.assert_invalid_address("DAeiBSH4nudXgoxS4kY6uhTPobc7AlrWDA")
        self.assert_invalid_address("DRbnCYbuMXdKU4y8dya9EnocL47gFjErWeg")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCBODnG6Rc")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCB0DnG6Rc")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCBIDnG6Rc")


if __name__ == '__main__':
    unittest.main()