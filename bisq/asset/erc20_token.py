from abc import ABC
from typing import TYPE_CHECKING

from bisq.asset.ether_address_validator import EtherAddressValidator
from bisq.asset.token import Token

if TYPE_CHECKING:
    from bisq.asset.address_validator import AddressValidator


class Erc20Token(Token, ABC):
    """
    Abstract base class for Ethereum-based Tokens that implement the
    [ERC-20 Token Standard](https://theethereum.wiki/w/index.php/ERC20_Token_Standard)
    
    since: 0.7.0
    """

    def __init__(
        self,
        name: str,
        ticker_symbol: str,
    ):
        super().__init__(name, ticker_symbol, EtherAddressValidator())
    
