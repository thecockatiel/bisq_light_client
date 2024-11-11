import unittest
from bisq.asset.coins.mask import Mask
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class MaskTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Mask())

    def test_valid_addresses(self):
        self.assert_valid_address("MbxYjp38aUXBuESwsFv8YmRvbQvMhNyJygU6ViLCjM4sUNqFjsHQim9dvzp9p8BVTjdsRkVNrC1Zy3NJRb18hav3CPe5eWn")
        self.assert_valid_address("MeGcanFnSr4bJFuNoHogCBdDCsqDrNu5njPc1Yh1DfsTUTL5dLbbtE119f4vztxXu6fFCKWRmpqjABdDyGrzMDkhTC38WwS")
        self.assert_valid_address("bTWEbW8kKVrZkDwyPs5t7BZXotMNyz5UY2QDJ6MjKT7ihA8kNKhoHDqPUiUB7jPxNpXLFkJsgL6TA1fo7yAzVUdm1hTopCocf")
        self.assert_valid_address("bTXejHgtfTLWzhyz9fHHBDKTWrsM8MKnebZCKeue8mbDWaKRhnQ8VisGRXUgTvUhsDiwX6PxeP5A22DFf5UVEk431Vjt8m3GM")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("") 
        self.assert_invalid_address("MsopefFnSr4bJFuNoHogCBdDCsqDrNu5Pc1Yh1DfsTUTL5dLbbtE119f4vztxXu6fFCKWRmpqjABdDyGrzMDkhTC38gWw")
        self.assert_invalid_address("MeGcanuyt4bJFuNoHogCBdDCsqDrNu5njPc1Yh1DfsTUTL5dLbbtE119f4vztxXu6fFCKWRmpqujABdDyGrzMDkhTC38WwSx")
        self.assert_invalid_address("MrtcanFnSr4bJFuNoHogCBdDCsqDrNu5Pc1Yh1DfsTUTL5dLbbtE119f4vztxXu6fFCKWRmpqjABdDyGrzMDkhTC3rt4vb8Ww")
        self.assert_invalid_address("bBXejHgtfTLWzhyz9fHKBDKTWrsM8MKnebZCKeue8mbDWaKRhnQ8VisGRXUgTvUhsDiwX6PxeP5A22DFf5UVEk431Vjt8m3GM")

if __name__ == "__main__":
    unittest.main()
