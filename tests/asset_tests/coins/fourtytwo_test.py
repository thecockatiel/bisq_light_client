import unittest

from bisq.asset.coins.fourty_two import FourtyTwo
from tests.asset_tests.abstract_asset_test import AbstractAssetTest
 
class FourtyTwoTest(AbstractAssetTest):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName, FourtyTwo())
    
    def test_valid_addresses(self):
        self.assert_valid_address("foUrDvc6vtJYMvqpx4oydJjL445udJ83M8rAqpkF8hEcbyLCp5MhvLaLGXtVYkqVXDG8YEpGBU7F241FtWXVCFEK7EMgnjrsM8")
        self.assert_valid_address("foUrFDEDkMGjV4HJzgYqSHhPTFaHfcpLM4WGZjYQZyrcCgyZs32QweCZEysK8eNxgsWdXv3YBP8QWDDWBAPu55eJ6gLf2TubwG")
        self.assert_valid_address("SNakeyQFcEacGHFaCgj4VpdfM3VTsFDygNHswx3CtKpn8uD1DmrbFwfM11cSyv3CZrNNWh4AALYuGS4U4pxYPHTiBn2DUJASoQw4B")

    def test_invalid_addresses(self):
        self.assert_invalid_address("")
        self.assert_invalid_address("fUrDvc6vtJYMvqpx4oydJjL445udJ83M8rAqpkF8hEcbyLCp5MhvLaLGXtVYkqVXDG8YEpGBU7F241FtWXVCFEK7EMgnjrsM8")
        self.assert_invalid_address("UrFDEDkMGjV4HJzgYqSHhPTFaHfcpLM4WGZjYQZyrcCgyZs32QweCZEysK8eNxgsWdXv3YBP8QWDDWBAPu55eJ6gLf2TubwG")
        self.assert_invalid_address("keyQFcEacGHFaCgj4VpdfM3VTsFDygNHswx3CtKpn8uD1DmrbFwfM11cSyv3CZrNNWh4AALYuGS4U4pxYPHTiBn2DUJASoQw4B")
        self.assert_invalid_address("akeyQFcEacGHFaCgj4VpdfM3VTsFDygNHswx3CtKpn8uD1DmrbFwfM11cSyv3CZrNNWh4AALYuGS4U4pxYPHTiBn2DUJASoQw4B")


if __name__ == '__main__':
    unittest.main()