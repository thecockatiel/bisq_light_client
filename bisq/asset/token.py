from abc import ABC
from typing import TYPE_CHECKING

from bisq.asset.abstract_asset import AbstractAsset

if TYPE_CHECKING:
    from bisq.asset.address_validator import AddressValidator


class Token(AbstractAsset, ABC):
    """
    Abstract base class for Assets that do not have their own dedicated blockchain,
    but are rather based on or derived from another blockchain. Contrast with Coin.
    Note that this is essentially a "marker" base class in the sense that it (currently)
    exposes no additional information or functionality beyond that found in
    AbstractAsset, but it is nevertheless useful in distinguishing between major
    different Asset types.

    since: 0.7.0
    """

    def __init__(
        self,
        name: str,
        ticker_symbol: str,
        address_validator: "AddressValidator",
    ):
        super().__init__(name, ticker_symbol, address_validator)

