import unittest
from bisq.asset.coins.veil import Veil
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class VeilTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Veil())

    def test_valid_addresses(self):
        self.assert_valid_address("VS2oF2pouKoLPJCjY8D7E1dStmUtitACu7")
        self.assert_valid_address("VV8VtpWTsYFBnhnvgQVnTvqoTx7XRRevte")
        self.assert_valid_address("VRZF4Am891FS224uuNirsrEugqMyg3VxjJ")

    def test_invalid_addresses(self):
        self.assert_invalid_address("17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhemqq")
        self.assert_invalid_address("3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX")
        self.assert_invalid_address("DRbnCYbuMXdKU4y8dya9EnocL47gFjErWeg")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCBODnG6Rc")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCB0DnG6Rc")
        self.assert_invalid_address("DTPAqTryNRCE2FgsxzohTtJXfCBIDnG6Rc")


if __name__ == "__main__":
    unittest.main()
