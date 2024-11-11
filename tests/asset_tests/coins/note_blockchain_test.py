import unittest
from bisq.asset.coins.note_blockchain import NoteBlockchain
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class NoteBlockchainTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, NoteBlockchain())
    
    def test_valid_addresses(self):
        self.assert_valid_address("NaeSp6oTDFiGBZejFyYJvuCaSqWMnMM44E")
        self.assert_valid_address("NPCz6bsSnksLUGbp11hbHFWqFuVweEgMWM")
        self.assert_valid_address("NMNA6oMBExWhYoVEcD2BbcL6qmQ6rs7GN2")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("1NMNA6oMBExWhYoVEcD2BbcL6qmQ6rs7GN2")
        self.assert_invalid_address("NMNA6oMBExyWhYoVEcD2BbcL6qmQ6rs7GN2")
        self.assert_invalid_address("NMNA6oMBExWhYoVEcD2BbcL6qmQ6rs7GN2#")


if __name__ == '__main__':
    unittest.main()