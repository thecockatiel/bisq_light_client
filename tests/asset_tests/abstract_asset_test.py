from abc import ABC, abstractmethod
import unittest

from bisq.asset.asset import Asset
from bisq.common.config.config import Config
from bisq.core.locale.res import Res 
 
class AbstractAssetTest(unittest.TestCase, ABC):
    
    def __init__(self, methodName='runTest', asset: Asset = None) -> None:
        super().__init__(methodName)
        Res.setup(Config())
        self.asset = asset
    
    def setUp(self) -> None:
        if self.asset is None:
            raise unittest.SkipTest("abstract class: asset is none")
        
    def assert_valid_address(self, address: str):
        result = self.asset.validate_address(address)
        self.assertEqual(result.is_valid, True, result.get_message())
        
    def assert_invalid_address(self, address: str):
        result = self.asset.validate_address(address)
        self.assertEqual(result.is_valid, False)
        
    def test_blank(self):
        self.assert_invalid_address("")
        
    def _has_same_ticker_symbol(self, other: Asset):
        """used in test_presence_in_asset_registry"""
        self.assertEqual(self.asset.get_ticker_symbol(), other.get_ticker_symbol())
        
    def test_presence_in_asset_registry(self):
        # TODO: implement this
        pass
        
    def test_valid_addresses(self):
        pass
    
    def test_invalid_addresses(self):
        pass