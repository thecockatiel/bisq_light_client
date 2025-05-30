from typing import TYPE_CHECKING
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bitcoinj.core.transaction import Transaction

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
    from bisq.core.btc.setup.wallets_setup import WalletsSetup


# TODO
class WalletsManager:
    def __init__(
        self,
        btc_wallet_service: "BtcWalletService",
        trade_wallet_service: "TradeWalletService",
        bsq_wallet_service: "BsqWalletService",
        wallets_setup: "WalletsSetup",
    ):
        self.btc_wallet_service = btc_wallet_service
        self.trade_wallet_service = trade_wallet_service
        self.bsq_wallet_service = bsq_wallet_service
        self.wallets_setup = wallets_setup

    def are_wallets_encrypted(self):
        return (
            self.are_wallets_available()
            and self.btc_wallet_service.is_encrypted
            and self.bsq_wallet_service.is_encrypted
        )

    def are_wallets_available(self):
        return (
            self.btc_wallet_service.is_wallet_ready
            and self.bsq_wallet_service.is_wallet_ready
        )

    def set_password(self, password: str):
        self.btc_wallet_service.password = password
        self.bsq_wallet_service.password = password
        self.trade_wallet_service.set_password(password)

    def maybe_add_segwit_keychains(self, aes_key: bytes):
        pass  # no need to implement

    # A bsq tx has miner fees in btc included. Thus we need to handle it on both wallets.
    def publish_and_commit_bsq_tx(
        self, tx: "Transaction", tx_type: "TxType", callback: "TxBroadcasterCallback"
    ):
        # We clone before commit to avoid unwanted side effects
        cloned_tx = self.btc_wallet_service.get_cloned_transaction(tx)
        self.btc_wallet_service.commit_tx(cloned_tx)
        self.bsq_wallet_service.commit_tx(tx, tx_type)

        self.bsq_wallet_service.broadcast_tx(tx, callback)
