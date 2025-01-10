from typing import TYPE_CHECKING, Optional
from bitcoinj.base.coin import Coin

if TYPE_CHECKING:
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction import Transaction


class BalanceListener:
    def __init__(self, address: Optional["Address"] = None):
        self.address = address

    def get_address(self) -> Optional["Address"]:
        return self.address

    def on_balance_changed(self, balance: Coin, tx: "Transaction") -> None:
        pass
