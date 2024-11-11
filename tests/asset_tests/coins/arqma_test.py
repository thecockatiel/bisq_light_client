import unittest

from bisq.asset.coins.arqma import Arqma
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class ArqmaTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Arqma())
    
    def test_valid_addresses(self):
        self.assert_valid_address("ar3ZLUTSac5DhxhyLJB11gcXWLYPKJchg7c8hoaKmqchC9TtHEdXzxGgt2vzCLUYwtSvkJQTXNCjzCR7KZiFUySV138PEopVC")
        self.assert_valid_address("aRS3V2hXuVAGAb5XWcDvN7McsSyqrEZ3XWyfMdEDCqioWNmVUuoKyNxDo7rwPCg55Ugb6KHXLN7hLZEGcnZzbm8M7uJ9YdVpeN")
        self.assert_valid_address("ar3mXR6SQeC3P9Dmq2LGsAeq5eDvjiNnYaywtqdNzixe6xLr38DiNVaaRKMkAQkR3NV3TuVAwAwEGH3QDgXJF3th1RwxABa9a")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("ar3ZLUTSac5DhxhyLJB11gcXWLYPKJchg7c8hoaKmqchC9TtHEdXzxGgt2vzCLUYwtSvkJQTXNCjzCR7KZiFUySV138PEopV")
        self.assert_invalid_address("aRS3V2hXuVAGAb5XWcDvN7McsSyqrEZ3XWyfMdEDCqioWNmVUuoKyNxDo7rwPCg55Ugb6KHXLN7hLZEGcnZzbm8M7uJ9YdVpeNZz")
        self.assert_invalid_address("aRV3V2hXuVAGAb5XWcDvN7McsSyqrEZ3XWyfMdEDCqioWNmVUuoKyNxDo7rwPCg55Ugb6KHXLN7hLZEGcnZzbm8M7uJ9YdVpeN")
        self.assert_invalid_address("ar3mXR6SQeC3P9Dmq2LGsAeq5eDvjiNnYaywtqdNzi#exLr38DiNVaaRKMkAQkR3NV3TuVAwAwEGH3QDgXJF3th1RwxABa9a")


if __name__ == '__main__':
    unittest.main()