import unittest
from bisq.asset.coins.lytix import Lytix
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class LytixTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Lytix())

    def test_valid_addresses(self): 
         self.assert_valid_address("8hTBZgtuexiUVMxCPcrPgMem7jurB2YJds")
         self.assert_valid_address("8hqgpDE5uSuyRrDMXo1w3y59SCxfv8sSsf")
         self.assert_valid_address("8wtCT2JHu4wd4JqCwxnWFQXhmggnwdjpSn")
         self.assert_valid_address("8pYVReruVqYdp6LRhsy63nuVgsg9Rx7FJT")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("6pYVReruVqYdp6LRhsy63nuVgsg9Rx7FJT")
        self.assert_invalid_address("8mgfRRiHVxf4JZH3pvffuY6NrKhffh13Q")
        self.assert_invalid_address("8j75cPWABNXdZ62u6ZfF4tDQ1tVdvJx2oh7")
        self.assert_invalid_address("FryiHzNPFatNV15hTurq9iFWeHTrQhUhG6")
        self.assert_invalid_address("8ryiHzNPFatNV15hTurq9iFWefffQhUhG6")
        self.assert_invalid_address("8ryigz2PFatNV15hTurq9iFWeHTrQhUhG1")

if __name__ == "__main__":
    unittest.main()
