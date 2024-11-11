import unittest
from bisq.asset.coins.iridium import Iridium
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class IridumTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Iridium())
    
    def test_valid_addresses(self):
        self.assert_valid_address("ir2oHYW7MbBQuMzTELg5o6FRqXNwWCU1wNzFsJG3VUCT9qMwayNsdwaQ85NHC3vLFSQ1eWtAPsYpvV4tXpnXKM9M377BW5KQ4")
        self.assert_valid_address("ir2PK6y3hjq9wLqdTQnPQ2FXhCJqJ1pKXNXezZUqeUWbTb3T74Xqiy1Yqwtkgri934C1E9Ba2quJDDh75nxDqEQj1K8i9DQXf")
        self.assert_valid_address("ir3steHWr1FRbtpjWWCAaxhzNggzJK6tqBy3qFw32YGV4CJdRsgYrpLifA7ivGdgZGNRKbRtYUp9GKvxnFSRFWTt2XuWunRYb")

    def test_invalid_addresses(self):
        self.assert_invalid_address("ir2oHYW7MbBQuMzTELg5o6FRqXNwWCU1wNzFsJG3VUCT9qMwayNsdwaQ85NHC3vLFSQ1eWtAPsYpvV4tXpnXKM9M377BW5KQ4t")
        self.assert_invalid_address("ir2PK6y3hjq9wLqdTQnPQ2FXhCJqJ1pKXNXezZUqeUWb#Tb3T74Xqiy1Yqwtkgri934C1E9Ba2quJDDh75nxDqEQj1K8i9DQXf")
        self.assert_invalid_address("")


if __name__ == '__main__':
    unittest.main()