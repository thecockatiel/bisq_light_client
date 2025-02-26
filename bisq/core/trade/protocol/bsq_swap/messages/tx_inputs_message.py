from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from bisq.core.btc.raw_transaction_input import RawTransactionInput


@runtime_checkable
class TxInputsMessage(Protocol):
    bsq_inputs: list["RawTransactionInput"]
    bsq_change: int
    buyers_btc_payout_address: str
    buyers_bsq_change_address: str
