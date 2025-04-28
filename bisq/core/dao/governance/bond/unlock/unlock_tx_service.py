from collections.abc import Callable
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING

from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.state.dao_state_service import DaoStateService


class UnlockTxService:
    """Service for publishing the unlock transaction."""

    def __init__(
        self,
        wallets_manager: "WalletsManager",
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
        dao_state_sevice: "DaoStateService",
    ):
        self.logger = get_ctx_logger(__name__)
        self._wallets_manager = wallets_manager
        self._bsq_wallet_service = bsq_wallet_service
        self._btc_wallet_service = btc_wallet_service
        self._dao_state_sevice = dao_state_sevice

    def publish_unlock_tx(
        self,
        lockup_tx_id: str,
        result_handler: Callable[[str], None],
        exception_handler: Callable[[Exception], None],
    ):
        try:

            class Listener(TxBroadcasterCallback):
                def on_success(self_, tx: "Transaction"):
                    result_handler(tx.get_tx_id())

                def on_failure(self_, exception):
                    exception_handler(exception)

            unlock_tx = self._get_unlock_tx(lockup_tx_id)
            self._wallets_manager.publish_and_commit_bsq_tx(
                unlock_tx,
                TxType.UNLOCK,
                Listener(),
            )
        except Exception as e:
            exception_handler(e)

    def get_mining_fee_and_tx_vsize(
        self,
        lockup_tx_id: str,
    ) -> tuple[Coin, int]:
        transaction = self._get_unlock_tx(lockup_tx_id)
        mining_fee = transaction.get_fee()
        tx_vsize = transaction.get_vsize()
        return mining_fee, tx_vsize

    def _get_unlock_tx(
        self,
        lockup_tx_id: str,
    ) -> "Transaction":
        lockup_tx_output = self._dao_state_sevice.get_lockup_tx_output(lockup_tx_id)
        check_argument(lockup_tx_output is not None, "lockupTxOutput must be present")
        prepared_tx = self._bsq_wallet_service.get_prepared_unlock_tx(lockup_tx_output)
        tx_with_btc_fee = self._btc_wallet_service.complete_prepared_bsq_tx(
            prepared_tx, None
        )
        transaction = self._bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
            tx_with_btc_fee
        )
        self.logger.info(f"Unlock tx: {transaction}")
        return transaction
