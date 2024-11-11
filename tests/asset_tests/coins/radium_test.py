import unittest
from bisq.asset.coins.radium import Radium
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class RadiumTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Radium())

    def test_valid_addresses(self):
        self.assert_valid_address("XfrvQw3Uv4oGgc535TYyBCT2uNU7ofHGDU")
        self.assert_valid_address("Xwgof4wf1t8TnQUJ2UokZRVwHxRt4t6Feb")
        self.assert_valid_address("Xep8KxEZUsCxQuvCfPdt2VHuHbp43nX7Pm")

    def test_invalid_addresses(self):
        self.assert_invalid_address("1LgfapHEPhZbRF9pMd5WPT35hFXcZS1USrW")
        self.assert_invalid_address("1K5B7SDcuZvd2oUTaW9d62gwqsZkteXqA4")
        self.assert_invalid_address("1GckU1XSCknLBcTGnayBVRjNsDjxqopNav")


if __name__ == "__main__":
    unittest.main()
