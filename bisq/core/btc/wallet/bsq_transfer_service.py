from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.btc.model.bsq_transfer_model import BsqTransferModel
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager


class BsqTransferService:

    def __init__(
        self,
        wallets_manager: "WalletsManager",
        bsq_wallet_service: "BsqWalletService",
        btc_wallet_service: "BtcWalletService",
    ):
        self.logger = get_ctx_logger(__name__)
        self.wallets_manager = wallets_manager
        self.bsq_wallet_service = bsq_wallet_service
        self.btc_wallet_service = btc_wallet_service

    def get_bsq_transfer_model(
        self, address: "Address", receiver_amount: "Coin", tx_fee_per_vbyte: "Coin"
    ) -> BsqTransferModel:
        prepared_send_tx = self.bsq_wallet_service.get_prepared_send_bsq_tx(
            str(address), receiver_amount
        )
        tx_with_btc_fee = self.btc_wallet_service.complete_prepared_send_bsq_tx(
            prepared_send_tx, tx_fee_per_vbyte
        )
        signed_tx = self.bsq_wallet_service.sign_tx_and_verify_no_dust_outputs(
            tx_with_btc_fee
        )

        return BsqTransferModel(
            address, receiver_amount, prepared_send_tx, tx_with_btc_fee, signed_tx
        )

    def send_funds(
        self, bsq_transfer_model: "BsqTransferModel", callback: TxBroadcasterCallback
    ):
        self.logger.info(f"Publishing BSQ transfer {bsq_transfer_model.to_short_string()}")
        self.wallets_manager.publish_and_commit_bsq_tx(
            bsq_transfer_model.tx_with_btc_fee, bsq_transfer_model.tx_type, callback
        )
