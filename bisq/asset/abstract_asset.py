from abc import ABC
from typing import TYPE_CHECKING

from bisq.asset.asset import Asset

if TYPE_CHECKING:
    from bisq.asset.address_validation_result import AddressValidationResult
    from bisq.asset.address_validator import AddressValidator

class AbstractAsset(Asset, ABC):
    """
    Abstract base class for Asset implementations.
    Most implementations should extend Coin, Token or their subtypes instead.
    """

    def __init__(
        self, name: str, ticker_symbol: str, address_validator: "AddressValidator"
    ):
        if not name or not name.strip():
            raise ValueError("Name cannot be blank")
        if not ticker_symbol or not ticker_symbol.strip():
            raise ValueError("Ticker symbol cannot be blank")
        if address_validator is None:
            raise ValueError("Address validator cannot be None")
        self.name = name
        self.ticker_symbol = ticker_symbol
        self.address_validator = address_validator

    def get_name(self) -> str:
        return self.name

    def get_ticker_symbol(self) -> str:
        return self.ticker_symbol

    def validate_address(self, address: str) -> "AddressValidationResult":
        return self.address_validator.validate(address)

    def __str__(self) -> str:
        return self.__class__.__name__
