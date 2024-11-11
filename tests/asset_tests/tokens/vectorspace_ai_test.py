import unittest

from bisq.asset.tokens.vectorspace_ai import VectorspaceAI
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class VectorspaceAITest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, VectorspaceAI())
    
    def test_valid_addresses(self):
        self.assert_valid_address("0xdd88dbdde30b684798881d4f3d9a3752d6c1dd71")
        self.assert_valid_address("dd88dbdde30b684798881d4f3d9a3752d6c1dd71")

    def test_invalid_addresses(self):
        self.assert_invalid_address("0x2ecf455d8a2e6baf8d1039204c4f97efeddf27a82")
        self.assert_invalid_address("0xh8wheG1jdka0c8b8263758chanbmshj2937zgab")
        self.assert_invalid_address("h8wheG1jdka0c8b8263758chanbmshj2937zgab")

if __name__ == '__main__':
    unittest.main()