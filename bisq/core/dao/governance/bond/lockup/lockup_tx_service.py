from collections.abc import Callable
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING

from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.bond.lockup.lockup_reason import LockupReason
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager


class LockupTxService:
    """Service for publishing the lockup transaction."""

    def __init__(
        self,
        wallets_manager: "WalletsManager",
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
    ):
        self.logger = get_ctx_logger(__name__)
        self._wallets_manager = wallets_manager
        self._bsq_wallet_service = bsq_wallet_service
        self._btc_wallet_service = btc_wallet_service

    def publish_lockup_tx(
        self,
        lockup_amount: Coin,
        lock_time: int,
        lockup_reason: LockupReason,
        hash: bytes,
        result_handler: Callable[[str], None],
        exception_handler: Callable[[Exception], None],
    ):
        check_argument(
            BondConsensus.MIN_LOCK_TIME <= lock_time <= BondConsensus.MAX_LOCK_TIME,
            "lockTime not in range",
        )
        try:
            lockup_tx = self._get_lockup_tx(
                lockup_amount, lock_time, lockup_reason, hash
            )

            class Listener(TxBroadcasterCallback):
                def on_success(self_, tx: "Transaction"):
                    result_handler(tx.get_tx_id())

                def on_failure(self_, exception):
                    exception_handler(exception)

            self._wallets_manager.publish_and_commit_bsq_tx(
                lockup_tx,
                TxType.LOCKUP,
                Listener(),
            )
        except Exception as e:
            exception_handler(e)

    def get_mining_fee_and_tx_vsize(
        self,
        lockup_amount: Coin,
        lock_time: int,
        lockup_reason: LockupReason,
        hash: bytes,
    ) -> tuple[Coin, int]:
        transaction = self._get_lockup_tx(lockup_amount, lock_time, lockup_reason, hash)
        mining_fee = transaction.get_fee()
        tx_vsize = transaction.get_vsize()
        return mining_fee, tx_vsize

    def _get_lockup_tx(
        self,
        lockup_amount: Coin,
        lock_time: int,
        lockup_reason: LockupReason,
        hash: bytes,
    ) -> "Transaction":
        op_return_data = BondConsensus.get_lockup_op_return_data(
            lock_time, lockup_reason, hash
        )
        prepared_tx = self._bsq_wallet_service.get_prepared_lockup_tx(lockup_amount)
        tx_with_btc_fee = self._btc_wallet_service.complete_prepared_bsq_tx(
            prepared_tx, op_return_data
        )
        transaction = self._bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
            tx_with_btc_fee
        )
        self.logger.info(f"Lockup tx: {transaction}")
        return transaction
