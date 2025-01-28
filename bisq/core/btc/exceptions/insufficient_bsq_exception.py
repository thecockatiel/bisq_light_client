from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException


class InsufficientBsqException(InsufficientMoneyException):
    def __init__(self, missing: Coin):
        super().__init__(
            missing, f"Insufficient BSQ, missing {missing.value / 100} BSQ"
        )
