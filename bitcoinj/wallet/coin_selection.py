from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bitcoinj.base.coin import Coin
    from bitcoinj.core.transaction_output import TransactionOutput


class CoinSelection:
    """
    Represents the results of a CoinSelector#select(Coin, List) operation. A coin selection represents a list
    of spendable transaction outputs that sum together to a total value gathered. Different coin selections
    could be produced by different coin selectors from the same input set, according to their varying policies.
    """
    def __init__(
        self,
        gathered: list["TransactionOutput"],
    ):
        self.value_gathered = CoinSelection.sum_output_values(gathered)
        self.gathered = tuple(gathered)

    @staticmethod
    def sum_output_values(outputs: list["TransactionOutput"]):
        return sum((output.get_value() for output in outputs), Coin.ZERO())
