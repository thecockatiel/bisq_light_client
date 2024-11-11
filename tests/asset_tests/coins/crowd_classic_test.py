import unittest
from bisq.asset.coins.crowd_classic import CRowdCLassic
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class CRowdCLassicTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, CRowdCLassic())
    
    def test_valid_addresses(self): 
        self.assert_valid_address("CfvddKQHdd975N5XQgmpVGTuK9mumvDBQo")
        self.assert_valid_address("CfvddKQHdd975N5XQgmpVGTuK9mumvDBQo") 

    def test_invalid_addresses(self): 
        self.assert_invalid_address("0xmnuL9poRmnuLd55bzKe7t48xtYv2bRES")
        self.assert_invalid_address("cvaAgcLKrno2AC7kYhHVDC")
        self.assert_invalid_address("19p49poRmnuLdnu55bzKe7t48xtYv2bRES")
        self.assert_invalid_address("csabbfjqwr12fbdf2gvffbdb12vdssdcaa")

if __name__ == '__main__':
    unittest.main()