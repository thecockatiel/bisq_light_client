import unittest

from bisq.asset.coins.adeptio import Adeptio
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class AdeptioTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Adeptio())
    
    def test_valid_addresses(self):
        self.assert_valid_address("AP7rSyQMZRek9HGy9QB1bpung69xViesN7")
        self.assert_valid_address("AWVXtnMo4pS2vBSNrBPLVvMgYvJGD6gSXk")
        self.assert_valid_address("AHq8sM8DEeFoZXeDkaimfCLtnMuuSWXFE7")
        self.assert_valid_address("ANG52tPNJuVknLQiLUdzVFoZ3vyo8UzkDL")

    def test_invalid_addresses(self):
        self.assert_invalid_address("aP7rSyQMZRek9HGy9QB1bpung69xViesN7")
        self.assert_invalid_address("DAeiBSH4nudXgoxS4kY6uhTPobc7AlrWDA")
        self.assert_invalid_address("BGhVYBXk511m8TPvQA6YokzxdpdhRE3sG6")
        self.assert_invalid_address("AZt2Kuy9cWFbTc888HNphppkuCTNyqu5PY")
        self.assert_invalid_address("AbosH98t3TRKzyNb8pPQV9boupVcBAX6of")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCBIDnG6Rc")


if __name__ == '__main__':
    unittest.main()