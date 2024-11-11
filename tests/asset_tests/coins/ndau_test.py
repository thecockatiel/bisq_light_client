import unittest
from bisq.asset.coins.ndau import Ndau
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class NdauTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Ndau())
    
    def test_valid_addresses(self):
        self.assert_valid_address("ndaaacj4gbv5xgwikt6adcujqyvd37ksadj4mg9v3jqtbe9f")
        self.assert_valid_address("ndnbeju3vmcxf9n96rb652eaeri79anqz47budnw8vwv3nyv")
        self.assert_valid_address("ndeatpdkx5stu28n3v6pie96bma5k8pzbvbdpu8dchyn46nw")
        self.assert_valid_address("ndxix97gyubjrkqbu4a5m3kpxyz4qhap3c3ui7359pzskwv4")
        self.assert_valid_address("ndbjhkkcvj88beqcamr439z6d6icm5mjwth5r7vrgfbnxktr")
        self.assert_valid_address("ndmpdkab97bi4ea73scjh6xpt8njjjhha4rarpr2zzzrv88u")

    def test_invalid_addresses(self):  
        self.assert_invalid_address("ndaaacj4gbv5xgwikt6adcujqyvd37ksadj4mg9v3jqtbe9")
        self.assert_invalid_address("ndnbeju3vmcxf9n96rb652eaeri79anqz47budnw8vwv3nyvw")
        self.assert_invalid_address("ndpatpdkx5stu28n3v6pie96bma5k8pzbvbdpu8dchyn46nw")
        self.assert_invalid_address("ndx1x97gyubjrkqbu4a5m3kpxyz4qhap3c3ui7359pzskwv4")
        self.assert_invalid_address("ndbjhklcvj88beqcamr439z6d6icm5mjwth5r7vrgfbnxktr")
        self.assert_invalid_address("ndmpdkab97bi4ea73scjh6xpt8njjjhhaArarpr2zzzrv88u")


if __name__ == '__main__':
    unittest.main()