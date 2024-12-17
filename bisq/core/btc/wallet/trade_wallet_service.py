from typing import TYPE_CHECKING, Optional

from bitcoinj.base.coin import Coin


if TYPE_CHECKING:
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction import Transaction


# TODO
class TradeWalletService:

    def get_wallet_tx(self, tx_id: bytes) -> "Transaction":
        raise RuntimeError("TradeWalletService.get_wallet_tx Not implemented yet")

    def create_btc_trading_fee_tx(
        self,
        funding_address: "Address",
        reserved_for_trade_address: "Address",
        change_address: "Address",
        reserved_funds_for_offer: Coin,
        use_savings_wallet: bool,
        trading_fee: Coin,
        tx_fee: Coin,
        fee_receiver_address: str,
        do_broadcast: bool,
        callback: "TxBroadcasterCallback",
    ) -> "Transaction":

        raise RuntimeError(
            "TradeWalletService.create_btc_trading_fee_tx Not implemented yet"
        )

    def complete_bsq_trading_fee_tx(
        self,
        prepared_bsq_tx: "Transaction",
        funding_address: "Address",
        reserved_for_trade_address: "Address",
        change_address: "Address",
        reserved_funds_for_offer: Coin,
        use_savings_wallet: bool,
        tx_fee: Coin,
    ) -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.complete_bsq_trading_fee_tx Not implemented yet"
        )

    def commit_tx(self, tx: "Transaction") -> None:
        raise RuntimeError("TradeWalletService.commit_tx Not implemented yet")

    def get_cloned_transaction(self, tx: "Transaction") -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.get_cloned_transaction Not implemented yet"
        )

    def trader_sign_and_finalize_disputed_payout_tx(
        self,
        deposit_tx_serialized: bytes,
        arbitrator_signature: bytes,
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_address_string: str,
        seller_address_string: str,
        traders_multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        arbitrator_pub_key: bytes,
    ) -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.trader_sign_and_finalize_disputed_payout_tx Not implemented yet"
        )

    def broadcast_tx(self, tx: "Transaction", callback: "TxBroadcasterCallback", timeout_sec: Optional[int] = None) -> None:
        raise RuntimeError("TradeWalletService.broadcast_tx Not implemented yet")