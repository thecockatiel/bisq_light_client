import unittest

from bisq.asset.coins.donu import Donu
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DonuTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Donu())
    
    def test_valid_addresses(self):
        self.assert_valid_address("NS5cGWdERahJ11pn12GoV5Jb7nsLzdr3kP")
        self.assert_valid_address("NU7nCzyQiAtTxzXLnDsJu4NhwQqrnPyJZj")
        self.assert_valid_address("NeeAy35aQirpmTARHEXpP8uTmpPCcSD9Qn")
        self.assert_valid_address("NScgetCW5bqDTVWFH3EYNMtTo5RcvDxD6B")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhemqq")
        self.assert_invalid_address("NScgetCW5bqDTVWFH3EYNMtTo5Rc#DxD6B")
        self.assert_invalid_address("NeeAy35a0irpmTARHEXpP8uTmpPCcSD9Qn")
        self.assert_invalid_address("neeAy35aQirpmTARHEXpP8uTmpPCcSD9Qn")
        self.assert_invalid_address("NScgetCWRcvDxD6B")


if __name__ == '__main__':
    unittest.main()