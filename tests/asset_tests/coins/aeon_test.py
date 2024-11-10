import unittest

from bisq.asset.coins.aeon import Aeon
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class AeonTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Aeon())
    
    def test_valid_addresses(self):
        self.assert_valid_address("WmsSXcudnpRFjXr5qZzEY5AF64J6CpFKHYXJS92rF9WjHVjQvJxrmSGNQnSfwwJtGGeUMKvLYn5nz2yL9f6M4FN51Z5r8zt4C")
        self.assert_valid_address("XnY88EywrSDKiQkeeoq261dShCcz1vEDwgk3Wxz77AWf9JBBtDRMTD9Fe3BMFAVyMPY1sP44ovKKpi4UrAR26o661aAcATQ1k")
        self.assert_valid_address("Wmu42kYBnVJgDhBUPEtK5dicGPEtQLDUVWTHW74GYvTv1Zrki2DWqJuWKcWV4GVcqnEMgb1ZiufinCi7WXaGAmiM2Bugn9yTx")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("WmsSXcudnpRFjXr5qZzEY5AF64J6CpFKHYXJS92rF9WjHVjQvJxrmSGNQnSfwwJtGGeUMKvLYn5nz2yL9f6M4FN51Z5r8zt4")
        self.assert_invalid_address("XnY88EywrSDKiQkeeoq261dShCcz1vEDwgk3Wxz77AWf9JBBtDRMTD9Fe3BMFAVyMPY1sP44ovKKpi4UrAR26o661aAcATQ1kZz")
        self.assert_invalid_address("XaY88EywrSDKiQkeeoq261dShCcz1vEDwgk3Wxz77AWf9JBBtDRMTD9Fe3BMFAVyMPY1sP44ovKKpi4UrAR26o661aAcATQ1k")
        self.assert_invalid_address("Wmu42kYBnVJgDhBUPEtK5dicGPEtQLDUVWTHW74GYv#vZrki2DWqJuWKcWV4GVcqnEMgb1ZiufinCi7WXaGAmiM2Bugn9yTx")


if __name__ == '__main__':
    unittest.main()