from dataclasses import field, dataclass
from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    from bitcoinj.base.coin import Coin
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.wallet.coin_selection import CoinSelection


@dataclass
class FeeCalculation:
    best_coin_selection: Optional["CoinSelection"] = field(default=None)
    """Selected UTXOs to spend"""
    best_change_output: Optional["TransactionOutput"] = field(default=None)
    """Change output (may be null if no change)"""
    updated_output_values: list["Coin"] = field(default_factory=list)
    """List of output values adjusted downwards when recipients pay fees (may be null if no adjustment needed)."""
