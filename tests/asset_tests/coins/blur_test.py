import unittest

from bisq.asset.coins.blur import Blur
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class BlurTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Blur())
    
    def test_valid_addresses(self):
        self.assert_valid_address("bL3W1g1d12sbxQDTQ6q8bgU2bBp2rkfFFKfNvQuUQTHqgQHRaxKTHqK5Nqdm53BU3ibPnsqbdYAnnJMyqJ6FfN9m3CSZSNqDE")
        self.assert_valid_address("bL2zBGUBDkQdyYasdoAdvQCxWLa9Mk5Q1PW8Zk7S38vx9xu7T7NMPPWNfieXqUyswo544ZSB3C1n9jLMfsUvR6p91rnrSdx9h")
        self.assert_valid_address("Ry49oErHtqyHucxADDT2DfEJ9pRv2ciSpKV9XseCuWmx1PK1CZi4gbPKxhWBdtvLJNNc94c4yDutmZrD3WrsHPYV1nvE9X4Cc")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("bl4E2BCFY31DPLjeqF6Gu7TEUM5v2JwpmudFX64AubQtFDYEPBvgvQPzidaawDhjAmHeZSw92wEBnUfdfY5144Sad2ZCknZzC")
        self.assert_invalid_address("Ry49oErHtqyHucxADDT2DfEJ9pRv2ciSpKV9XseCuWmx1PK1CZi4gbPKxhWBdtvLJNNc94c4yDutmZrD3WrsHPYV1nvE9X40")
        self.assert_invalid_address("bLNHRh8pFh5Y14bhBVAoD4cvqHyoPsQJqB3dr49zoF6bNDFrts96tuuj#RoUKWRwpTHmYt4Kf78FES7LCXAXKXFf6bMsx1sdgz")
        self.assert_invalid_address("82zBGUBDkQdyYasdoAdvQCxWLa9Mk5Q1PW#8Zk7S38vx9xu7T7NMPPWNfieXqUyswo544ZSB3C1n9jLMfsUvR6p91rnrSdxwd")


if __name__ == '__main__':
    unittest.main()