import unittest

from bisq.asset.coins.ergo import Ergo
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class ErgoTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, Ergo())
    
    def test_valid_addresses(self):
        self.assert_valid_address("9fRAWhdxEsTcdb8PhGNrZfwqa65zfkuYHAMmkQLcic1gdLSV5vA")
        self.assert_valid_address("25qGdVWg2yyYho8uC1pLtc7KxFn4nEEAwD")
        self.assert_valid_address("23NL9a8ngN28ovtLiKLgHexcdTKBbUMLhH")
        self.assert_valid_address("7bwdkU5V8")
        self.assert_valid_address("BxKBaHkvrTvLZrDcZjcsxsF7aSsrN73ijeFZXtbj4CXZHHcvBtqSxQ")

    def test_invalid_addresses(self):
        self.assert_invalid_address("9fRAWhdxEsTcdb8PhGNrZfwqa65zfkuYHAMmkQLcic1gdLSV5vAaa")
        self.assert_invalid_address("25qGdVWg2yyYho8uC1pLtc7KxFn4nEEAwDaa")
        self.assert_invalid_address("23NL9a8ngN28ovtLiKLgHexcdTKBbUMLhHaa")
        self.assert_invalid_address("7bwdkU5V8aa")
        self.assert_invalid_address("BxKBaHkvrTvLZrDcZjcsxsF7aSsrN73ijeFZXtbj4CXZHHcvBtqSxQ#")


if __name__ == '__main__':
    unittest.main()