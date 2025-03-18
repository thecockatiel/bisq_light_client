from typing import TYPE_CHECKING, Optional

from bisq.common.config.config import Config
from bisq.core.btc.model.inputs_and_change_output import InputsAndChangeOutput
from bisq.core.btc.model.prepared_deposit_tx_and_maker_inputs import (
    PreparedDepositTxAndMakerInputs,
)
from bisq.core.btc.wallet.wallet_service import WalletService
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.wallet.wallet import Wallet
from utils.preconditions import check_not_none
from bitcoinj.core.transaction import Transaction


if TYPE_CHECKING:
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
    from bitcoinj.core.address import Address


# TODO
class TradeWalletService:
    MIN_DELAYED_PAYOUT_TX_FEE = Coin.value_of(1000)

    def __init__(self):
        self.wallet: Optional["Wallet"] = None
        self.password: Optional[str] = None

    @property
    def params(self):
        return Config.BASE_CURRENCY_NETWORK_VALUE.parameters

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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Deposit tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def taker_creates_deposit_tx_inputs(
        self,
        take_offer_fee_tx: "Transaction",
        input_amount: Coin,
        tx_fee: Coin,
    ) -> "InputsAndChangeOutput":
        raise RuntimeError(
            "TradeWalletService.taker_creates_deposit_tx_inputs Not implemented yet"
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

    def buyer_as_maker_creates_and_signs_deposit_tx(
        self,
        maker_input_amount: Coin,
        ms_output_amount: Coin,
        taker_raw_transaction_inputs: list["RawTransactionInput"],
        taker_change_output_value: int,
        taker_change_address_string: Optional[str],
        maker_address: "Address",
        maker_change_address: "Address",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "PreparedDepositTxAndMakerInputs":
        raise RuntimeError(
            "TradeWalletService.buyer_as_maker_creates_and_signs_deposit_tx Not implemented yet"
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

    def seller_adds_buyer_witnesses_to_deposit_tx(
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

    def create_delayed_unsigned_payout_tx(
        self,
        deposit_tx: "Transaction",
        receivers: list[tuple[int, str]],
        lock_time: int,
    ) -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.create_delayed_unsigned_payout_tx Not implemented yet"
        )

    def sign_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        prepared_deposit_tx: "Transaction",
        my_multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> bytes:
        raise RuntimeError(
            "TradeWalletService.sign_delayed_payout_tx Not implemented yet"
        )

    def finalize_unconnected_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        buyer_signature: bytes,
        seller_signature: bytes,
        value: Coin,
    ) -> "Transaction":
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
            input.get_value(),
        )

        WalletService.check_wallet_consistency(self.wallet)
        assert (
            input.connected_output is not None
        ), "input.connected_output must not be None"
        input.verify(input.connected_output)
        return delayed_payout_tx

    def buyer_signs_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address_string: str,
        seller_payout_address_string: str,
        multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> bytes:
        raise RuntimeError(
            "TradeWalletService.buyer_signs_payout_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_connected_out_point(self, raw_transaction_input: "RawTransactionInput"):
        return TransactionOutPoint.from_tx(
            Transaction(self.params, raw_transaction_input.parent_transaction),
            raw_transaction_input.index,
        )

    def is_p2wh(self, raw_transaction_input: "RawTransactionInput"):
        return ScriptPattern.is_p2wh(
            check_not_none(
                self._get_connected_out_point(raw_transaction_input).connected_output
            ).get_script_pub_key()
        )
