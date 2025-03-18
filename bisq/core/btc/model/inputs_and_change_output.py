from typing import TYPE_CHECKING, Optional
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.btc.raw_transaction_input import RawTransactionInput


class InputsAndChangeOutput:

    def __init__(
        self,
        raw_transaction_inputs: list["RawTransactionInput"],
        change_output_value: int,
        change_output_address: Optional[str] = None,
    ):
        check_argument(bool(raw_transaction_inputs), "raw_transaction_inputs is empty")

        self.raw_transaction_inputs = raw_transaction_inputs

        self.change_output_value = change_output_value
        """Is set to 0 in case we don't have an output"""

        self.change_output_address = change_output_address
