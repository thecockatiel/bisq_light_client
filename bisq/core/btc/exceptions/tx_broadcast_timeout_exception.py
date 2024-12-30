from typing import TYPE_CHECKING, Optional
from bisq.core.btc.exceptions.tx_broadcast_exception import TxBroadcastException

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.wallet.wallet import Wallet


class TxBroadcastTimeoutException(TxBroadcastException):
    def __init__(self, local_tx: "Transaction", delay: int, wallet: "Wallet"):
        """
        Args:
            local_tx: The tx we sent out
            delay: The timeout delay
            wallet: Wallet is needed if a client is calling wallet.commit_tx(tx)
        """
        super().__init__(
            f"The transaction was not broadcasted in {delay} "
            f"seconds. txId={local_tx.get_tx_id()}"
        )
        self._local_tx = local_tx
        self._delay = delay
        self._wallet = wallet

    @property
    def local_tx(self) -> "Optional[Transaction]":
        return self._local_tx

    @property
    def delay(self) -> int:
        return self._delay

    @property
    def wallet(self) -> "Wallet":
        return self._wallet

    def __str__(self) -> str:
        return (
            f"TxBroadcastTimeoutException{{\n"
            f"     local_tx={self._local_tx},\n"
            f"     delay={self._delay}\n"
            f"}} {super().__str__()}"
        )
