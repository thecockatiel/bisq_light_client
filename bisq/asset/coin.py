from abc import ABC
from enum import IntEnum
from typing import TYPE_CHECKING

from bisq.asset.abstract_asset import AbstractAsset

if TYPE_CHECKING:
    from bisq.asset.address_validator import AddressValidator


class Coin(AbstractAsset, ABC):
    """
    Abstract base class for Assets with their own dedicated blockchain, such as
    Bitcoin itself or one of its many derivatives, competitors and alternatives,
    often called "altcoins", such as Litecoin, Ether, Monero and Zcash.

    A Coin maintains information about which Network it may be used on. By default,
    coins are constructed for use on that coin's "main network" or "main blockchain",
    i.e. that they are "real" coins for use in a production environment.
    In testing scenarios, however, a coin may be constructed for use on "testnet" or "regtest"
    networks.

    since: 0.7.0
    """

    class Network(IntEnum):
        MAINNET = 0
        TESTNET = 1
        REGTEST = 2

    def __init__(
        self,
        name: str,
        ticker_symbol: str,
        address_validator: "AddressValidator",
        network: Network = Network.MAINNET,
    ):
        super().__init__(name, ticker_symbol, address_validator)
        self.network = network
