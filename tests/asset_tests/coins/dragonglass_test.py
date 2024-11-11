import unittest
from bisq.asset.coins.dragonglass import Dragonglass
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class DragonglassTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Dragonglass())
    
    def test_valid_addresses(self):
        self.assert_valid_address("dRGLhxvCtLk1vfSD3WmFzyTN5ph2gZYvkZfxvLSrcdry95x4PPJrCKBTKDEFZYTw4bCGqoiaUWxNd8B41vqXaTY72Vi2XcvikX")
        self.assert_valid_address("dRGLjS5v91tDd4GDZeahUj95nkXSNQs5DMY1YStLN2hSNWD67iZh7ED7oDw841Kx6oUYouZaXmBNFcqSptNZ4dL94CbZbF53jt")

    def test_invalid_addresses(self): 
        self.assert_invalid_address("dRGLjS5v91tDd4GDZeahUj95nkXSNQs5DMY1YStLN2hSNWD67iZh7ED7oDw841Kx6oUYouZaXmBNFcqSptNZ4dL94CbZbF53j")
        self.assert_invalid_address("dRGLjS5v91tDd4GDZeahUj95nkXSNQs5DMY1YStLN2hSNWD67iZh7ED7oDw841Ko6oUYouZaXmBNFcqSptNZ4dL94oUCifk4048")
        self.assert_invalid_address("DRGLhxvCtLk1vfSD3WmFzyTN5ph2gZYvkZfxvLSrcdry95x4PPJrCKBTKDEFZYTw4bCGqoiaUWxNd8B41vqXaTY72Vi2XcvikX")
        self.assert_invalid_address("drglhxvCtLk1vfSD3WmFzyTN5ph2gZYvkZfxvLSrcdry95x4PPJrCKBTKDEFZYTw4bCGqoiaUWxNd8B41vqXaTY72Vi2XcvikX")
        self.assert_invalid_address("dRgLjS5v91tDd4GDZeahUj95nkXSNQs5DMY1YStLN2hSNWD67iZh7ED7oDw841Kx6oUYouZaXmBNFcqSptNZ4dL94CbZbF53jt")
        self.assert_invalid_address("dRGlhxvCtLk1vfSD3WmFzyTN5ph2gZYvkZfxvLSrcdry95x4PPJrCKBTKDEFZYTw4bCGqoiaUWxNd8B41vqXaTY72Vi2XcvikX")


if __name__ == '__main__':
    unittest.main()