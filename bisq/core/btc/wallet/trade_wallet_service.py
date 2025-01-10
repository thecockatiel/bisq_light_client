from typing import TYPE_CHECKING, Optional

from bisq.core.btc.wallet.wallet_service import WalletService
from bitcoinj.base.coin import Coin
from bitcoinj.wallet.wallet import Wallet


if TYPE_CHECKING:
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction import Transaction


# TODO
class TradeWalletService:
    MIN_DELAYED_PAYOUT_TX_FEE = Coin.value_of(1000)
    
    def __init__(self):
        self.wallet: Optional["Wallet"] = None

    def get_wallet_tx(self, tx_id: str) -> "Transaction":
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

    def broadcast_tx(
        self,
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout_sec: Optional[int] = None,
    ) -> None:
        raise RuntimeError("TradeWalletService.broadcast_tx Not implemented yet")
    
    def seller_signs_and_finalizes_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_signature: bytes,
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin, 
        buyer_payout_address_string: str,
        seller_payout_address_string: str,
        multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.seller_signs_and_finalizes_payout_tx Not implemented yet"
        )

    def sign_mediated_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address_string: str,
        seller_payout_address_string: str,
        my_multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "bytes":
        raise RuntimeError(
            "TradeWalletService.sign_mediated_payout_tx Not implemented yet"
        )

    def finalize_mediated_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_signature: bytes,
        seller_signature: bytes,
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address: str,
        seller_payout_address: str,
        multi_sig_key_pair: "DeterministicKey",
        buyer_multi_sig_pub_key: bytes,
        seller_multi_sig_pub_key: bytes,
    ) -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.finalize_mediated_payout_tx Not implemented yet"
        )

    def seller_adds_buyer_witness_to_deposit_tx(
        self,
        my_deposit_tx: "Transaction",
        buyers_deposit_tx_with_witness: "Transaction",
    ) -> None:
        number_inputs = len(my_deposit_tx.inputs)
        for i in range(number_inputs):
            tx_input = my_deposit_tx.inputs[i]
            witness_from_buyer = buyers_deposit_tx_with_witness.inputs[i].witness

            if not tx_input.witness and witness_from_buyer:
                tx_input.witness = witness_from_buyer

    def finalize_unconnected_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        buyer_signature: bytes,
        seller_signature: bytes,
        value: Coin,
    ) -> None:
        raise RuntimeError(
            "TradeWalletService.finalize_unconnected_delayed_payout_tx Not implemented yet"
        )
    
    def finalize_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        buyer_signature: bytes,
        seller_signature: bytes,
    ) -> "Transaction":
        input = delayed_payout_tx.inputs[0]
        self.finalize_unconnected_delayed_payout_tx(
            delayed_payout_tx,
            buyer_pub_key,
            seller_pub_key,
            buyer_signature,
            seller_signature,
            input.value,
        )
        
        WalletService.check_wallet_consistency(self.wallet)
        assert input.connected_output is not None, "input.connected_output must not be None"
        input.verify(input.connected_output)
        return delayed_payout_tx