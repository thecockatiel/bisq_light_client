from bisq.common.setup.log_setup import get_ctx_logger
from utils.aio import FutureCallback, as_future
from datetime import timedelta
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.btc.exceptions.tx_broadcast_exception import TxBroadcastException
from bisq.core.btc.exceptions.tx_broadcast_timeout_exception import (
    TxBroadcastTimeoutException,
)
from bisq.core.btc.wallet.http.mem_pool_space_tx_broadcaster import (
    MemPoolSpaceTxBroadcaster,
)
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bitcoinj.core.transaction import Transaction
from bitcoinj.wallet.wallet import Wallet


class TxBroadcaster:
    DEFAULT_BROADCAST_TIMEOUT_SEC = 5
    broadcast_timer_map: dict[str, Timer] = {}

    @staticmethod
    def broadcast_tx(
        wallet: "Wallet",
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout_sec: float = None,
    ):
        logger = get_ctx_logger(__name__)
        if timeout_sec is None:
            timeout_sec = TxBroadcaster.DEFAULT_BROADCAST_TIMEOUT_SEC

        tx_id = tx.get_tx_id()
        logger.info(f"Txid: {tx_id} hex: {tx.bitcoin_serialize().hex()}")

        if tx_id not in TxBroadcaster.broadcast_timer_map:
            timeout_timer = UserThread.run_after(
                lambda: (
                    logger.warning(
                        f"Broadcast of tx {tx_id} not completed after {timeout_sec} sec."
                    ),
                    TxBroadcaster._stop_and_remove_timer(tx_id),
                    UserThread.execute(
                        lambda: callback.on_timeout(
                            TxBroadcastTimeoutException(tx, timeout_sec, wallet)
                        )
                    ),
                ),
                timedelta(seconds=timeout_sec),
            )
            TxBroadcaster.broadcast_timer_map[tx_id] = timeout_timer
        else:
            # Would be the wrong way how to use the API (calling 2 times a broadcast with same tx).
            # An arbitrator reported that got the error after a manual payout, need to investigate why...
            TxBroadcaster._stop_and_remove_timer(tx_id)
            UserThread.execute(
                lambda: callback.on_failure(
                    TxBroadcastException(
                        f"We got broadcastTx called with a tx which has an open timeoutTimer. txId={tx_id}",
                        tx_id=tx_id,
                    )
                )
            )

        # We decided the least risky scenario is to commit the tx to the wallet and broadcast it later.
        # If it's a bsq tx WalletManager.publishAndCommitBsqTx() should have committed the tx to both bsq and btc
        # wallets so the next line causes no effect.
        # If it's a btc tx, the next line adds the tx to the wallet.
        wallet.maybe_add_transaction(tx)

        def on_broadcast_success(res):
            # We expect that there is still a timeout in our map, otherwise the timeout got triggered
            if tx_id in TxBroadcaster.broadcast_timer_map:
                TxBroadcaster._stop_and_remove_timer(tx_id)
                # At regtest we get called immediately back but we want to make sure that the handler is not called
                # before the caller is finished.
                UserThread.execute(lambda: callback.on_success(tx))
            else:
                logger.warning(
                    f"We got an onSuccess callback for a broadcast which already triggered the timeout. txId={tx_id}"
                )

        def on_broadcast_failure(e: Exception):
            TxBroadcaster._stop_and_remove_timer(tx_id)
            UserThread.execute(
                lambda: callback.on_failure(
                    TxBroadcastException(
                        f"We got an onFailure from the peerGroup.broadcastTransaction callback.",
                        e,
                        tx_id,
                    )
                )
            )

        as_future(wallet.broadcast_tx(tx)).add_done_callback(
            FutureCallback(on_broadcast_success, on_broadcast_failure)
        )

        # For better redundancy in case the broadcast via Electrum fails we also
        # publish the tx via mempool nodes.
        # as_future(MemPoolSpaceTxBroadcaster.broadcast_tx(tx, wallet))

    @staticmethod
    def _stop_and_remove_timer(tx_id: str):
        timer = TxBroadcaster.broadcast_timer_map.get(tx_id, None)
        if timer is not None:
            timer.stop()
        TxBroadcaster.broadcast_timer_map.pop(tx_id, None)
