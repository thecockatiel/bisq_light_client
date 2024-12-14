from typing import Optional
from bitcoinj.base.coin import Coin


class InsufficientMoneyException(Exception):
    """Thrown to indicate that you don't have enough money available to perform the requested operation."""
    
    def __init__(self, missing: Optional[Coin] = None, message: Optional[str] = None):
        self.missing = missing
        if missing is not None and message is None:
            super().__init__(f"Insufficient money,  missing {missing.to_friendly_string()}")
        elif message is not None:
            super().__init__(message)


