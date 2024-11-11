import unittest
from bisq.asset.coins.remix import Remix
from tests.asset_tests.abstract_asset_test import AbstractAssetTest


class RemixTest(AbstractAssetTest):

    def __init__(self, methodName="runTest"):
        super().__init__(methodName, Remix())

    def test_valid_addresses(self):
        self.assert_valid_address("REMXisBbsyWKYdENidNhiP3bGaVwVgtescK2ZuJMtxed4TqJGH8VX57gMSTyfC43FULSM4XXzmj727SGjDNak16mGaYdban4o4m")
        self.assert_valid_address("REMXiqQhgfqWtZ1gfxP4iDbXEV4f8cUDFAp2Bz43PztJSJvv2mUqG4Z2YFBMauJV74YCDcJLyqkbCfsC55LNJhQfZxdiE5tGxKq")
        self.assert_valid_address("SubRM7BgZyGiccN3pKuRPrN52FraE9j7miu17MDwx6wWb7J6XWeDykk48JBZ3QVSXR7GJWr2RdpjK3YCRAUdTbfRL4wGAn7oggi")
        self.assert_valid_address("SubRM9N9dmoeawsXqNt94jVn6vSurYxxU3E6mEoMnzWvAMB7QjL3Zc9dmKTD64wE5ePFfACVLVLTZZa6GKVp6FuZ7Z9dJheMoJb")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("REMXiqQhgfqWtZ1gfxP4iDbXEV4f8cUDFAp2Bz43PztJSJvv2mUqG4Z2YFBMauJV74YCDcJLyqkbCfsC55LNJhQ")
        self.assert_invalid_address("REMXIqQhgfqWtZ1gfxP4iDbXEV4f8cUDFApdfgdfgdfgdfgr4453453453444JV74YCDcJLyqkbCfsC55LNJhQfZxdiE5tGxKq")
        self.assert_invalid_address("REMXiqQhgfqWtZ1gfxP4iDbXEV4f8cUDFAp2Bz43PztJS4dssdffffsdfsdfffffdfgdfgsaqkbCfsC4iDbXEV4f8cUDFAp2Bz")
        self.assert_invalid_address("SubRM9N9dmoeawsXqNt94jVn6vSurYxxU3E6mEoMnzWvAMB7QL3Zc9dmKTD64wE5ePFfACVLVLTZZa6GKVp6FuZ7Z9dJheMo69")
        self.assert_invalid_address("SubRM9N9dmoeawsXqNt94jdfsdfsdfsdfsdfsdfJb")
        self.assert_invalid_address("SubrM9N9dmoeawsXqNt94jVn6vSfeet")


if __name__ == "__main__":
    unittest.main()
