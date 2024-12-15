from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bisq.core.btc.exceptions.tx_broadcast_timeout_exception import (
        TxBroadcastTimeoutException,
    )
    from bisq.core.btc.exceptions.tx_broadcast_exception import TxBroadcastException
    from bitcoinj.core.transaction import Transaction

logger = get_logger(__name__)


class TxBroadcasterCallback(ABC):

    @abstractmethod
    def on_success(self, transaction: "Transaction"):
        pass

    @abstractmethod
    def on_failure(self, exception: "TxBroadcastException"):
        pass

    def on_timeout(self, exception: "TxBroadcastTimeoutException"):
        tx = exception.local_tx
        if tx:
            # We optimistically assume that the tx broadcast succeeds later and call onSuccess on the callback handler.
            # This behaviour carries less potential problems than if we would trigger a failure (e.g. which would cause
            # a failed create offer attempt or failed take offer attempt).
            # We have no guarantee how long it will take to get the information that sufficiently many BTC nodes have
            # reported back to BitcoinJ that the tx is in their mempool.
            # In normal situations that's very fast but in some cases it can take minutes (mostly related to Tor
            # connection issues). So if we just go on in the application logic and treat it as successful and the
            # tx will be broadcast successfully later all is fine.
            # If it will fail to get broadcast, it will lead to a failure state, the same as if we would trigger a
            # failure due the timeout.
            # So we can assume that this behaviour will lead to less problems as otherwise.
            # Long term we should implement better monitoring for Tor and the provided Bitcoin nodes to find out
            # why those delays happen and add some rollback behaviour to the app state in case the tx will never
            # get broadcast.
            logger.warning(f"TxBroadcaster.onTimeout called: {repr(exception)}")
            self.on_success(tx)
        else:
            logger.error(
                f"TxBroadcaster.onTimeout: Tx is null. exception={repr(exception)}"
            )
            self.on
