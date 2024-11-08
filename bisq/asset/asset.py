from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bisq.asset.address_validation_result import AddressValidationResult

# TODO: update comments after implementing AssetRegistery?
class Asset(ABC):
    """
    Interface representing a given ("crypto") asset in its most abstract form, having a
    name, eg "Bitcoin", a ticker symbol, eg "BTC", and an address validation function.
    Together, these properties represent the minimum information and functionality 
    required to register and trade an asset on the Bisq network.
    
    Implementations typically extend either the Coin or Token base
    classes, and must be registered in the services/bisq.asset.Asset file
    in order to be available in the AssetRegistry at runtime.
    
    since: 0.7.0
    """

    @abstractmethod 
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_ticker_symbol(self) -> str:
        pass

    @abstractmethod
    def validate_address(self, address: str) -> "AddressValidationResult":
        pass