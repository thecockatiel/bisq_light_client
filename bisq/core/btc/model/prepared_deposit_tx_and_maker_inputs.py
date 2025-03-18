from dataclasses import dataclass
from bisq.core.btc.raw_transaction_input import RawTransactionInput


@dataclass
class PreparedDepositTxAndMakerInputs:
    raw_maker_inputs: list[RawTransactionInput]
    deposit_transaction: bytes
