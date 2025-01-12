from abc import ABC, abstractmethod
from collections.abc import Callable

from bitcoinj.base.coin import Coin


class BsqBalanceListener(
    Callable[[Coin, Coin, Coin, Coin, Coin, Coin, Coin], None], ABC
):

    @abstractmethod
    def on_update_balances(
        self,
        available_balance: Coin,
        available_non_bsq_balance: Coin,
        unverified_balance: Coin,
        unconfirmed_change_balance: Coin,
        locked_for_voting_balance: Coin,
        locked_in_bonds_balance: Coin,
        unlocking_bonds_balance: Coin,
    ):
        pass

    def __call__(self, *args, **kwds):
        return self.on_update_balances(*args, **kwds)
