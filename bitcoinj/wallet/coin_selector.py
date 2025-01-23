from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from bitcoinj.base.coin import Coin
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.wallet.coin_selection import CoinSelection


class CoinSelector(ABC):
    """
    A CoinSelector is responsible for picking some outputs to spend, from the list of all possible outputs. It
    allows you to customize the policies for creation of transactions to suit your needs. The select operation
    may return a CoinSelection that has a valueGathered lower than the requested target, if there's not
    enough money in the wallet.
    """

    @abstractmethod
    def select(
        self, target: "Coin", candidates: List["TransactionOutput"]
    ) -> "CoinSelection":
        """Creates a CoinSelection that tries to meet the target amount of value"""
        pass
