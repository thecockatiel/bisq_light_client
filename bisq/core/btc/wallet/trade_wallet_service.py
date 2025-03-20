from typing import TYPE_CHECKING, Optional

from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.model.inputs_and_change_output import InputsAndChangeOutput
from bisq.core.btc.model.prepared_deposit_tx_and_maker_inputs import (
    PreparedDepositTxAndMakerInputs,
)
from bisq.core.btc.setup.wallet_config import WalletConfig
from bisq.core.btc.setup.wallets_setup import WalletsSetup
from bisq.core.btc.wallet.btc_coin_selector import BtcCoinSelector
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.btc.wallet.tx_broadcaster import TxBroadcaster
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.user.preferences import Preferences
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.wallet.send_request import SendRequest
from bitcoinj.wallet.wallet import Wallet
from utils.preconditions import check_not_none
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.address import Address


if TYPE_CHECKING:
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback


logger = get_logger(__name__)


# TODO
class TradeWalletService:
    MIN_DELAYED_PAYOUT_TX_FEE = Coin.value_of(1000)

    def __init__(self, wallets_setup: "WalletsSetup", preferences: "Preferences"):
        self._wallets_setup = wallets_setup
        self._preferences = preferences
        self._wallet_config: Optional["WalletConfig"] = None
        self._wallet: Optional["Wallet"] = None
        self._password: Optional[str] = None

        self._wallets_setup.add_setup_completed_handler(
            lambda: (
                setattr(self, "_wallet_config", self._wallets_setup.wallet_config),
                setattr(self, "_wallet", self._wallets_setup.btc_wallet),
            )
        )

    @property
    def params(self):
        return Config.BASE_CURRENCY_NETWORK_VALUE.parameters

    def set_password(self, password: str):
        self._password = password

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Trade fee
    # ///////////////////////////////////////////////////////////////////////////////////////////

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
        trading_fee_tx = Transaction(self.params)
        send_request = None
        try:
            trading_fee_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    trading_fee,
                    Address.from_string(self.params, fee_receiver_address),
                    trading_fee_tx,
                )
            )
            # the reserved amount we need for the trade we send to our trade reservedForTradeAddress
            trading_fee_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    reserved_funds_for_offer,
                    reserved_for_trade_address,
                    trading_fee_tx,
                )
            )

            # we allow spending of unconfirmed tx (double spend risk is low and usability would suffer if we need to
            # wait for 1 confirmation)
            # In case of double spend we will detect later in the trade process and use a ban score to penalize bad behaviour (not impl. yet)
            send_request = SendRequest.for_tx(trading_fee_tx)
            send_request.shuffle_outputs = False
            send_request.password = self._password
            if use_savings_wallet:
                send_request.coin_selector = BtcCoinSelector(
                    self._wallets_setup.get_addresses_by_context(
                        AddressEntryContext.AVAILABLE
                    ),
                    self._preferences.get_ignore_dust_threshold(),
                )
            else:
                send_request.coin_selector = BtcCoinSelector(
                    funding_address,
                    self._preferences.get_ignore_dust_threshold(),
                )
            # We use a fixed fee
            send_request.fee = tx_fee
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False

            # Change is optional in case of overpay or use of funds from savings wallet
            send_request.change_address = change_address

            check_not_none(self._wallet, "Wallet must not be None")
            self._wallet.complete_tx(send_request)

            if self._remove_dust(trading_fee_tx):
                self._wallet.sign_tx(self._password, trading_fee_tx)

            WalletService.print_tx("trading_fee_tx", trading_fee_tx)

            if do_broadcast and callback:
                self.broadcast_tx(trading_fee_tx, callback)

            return trading_fee_tx
        except Exception as e:
            if self._wallet and send_request and send_request.coin_selector:
                logger.error(
                    f"Balance for coin selector at create_btc_trading_fee_tx = {self._wallet.get_coin_selector_balance(send_request.coin_selector).to_friendly_string()}"
                )
            logger.error(
                f"create_btc_trading_fee_tx failed: trading_fee_tx={trading_fee_tx}, tx_outputs={trading_fee_tx.outputs}"
            )
            raise e

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

    def seller_as_maker_creates_deposit_tx(
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
            "TradeWalletService.seller_as_maker_creates_deposit_tx Not implemented yet"
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

    def taker_signs_deposit_tx(
        self,
        taker_is_seller: bool,
        makers_deposit_tx_serialized: bytes,
        ms_output_amount: Coin,
        buyer_inputs: list["RawTransactionInput"],
        seller_inputs: list["RawTransactionInput"],
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "Transaction":
        raise RuntimeError(
            "TradeWalletService.taker_signs_deposit_tx Not implemented yet"
        )

    def seller_as_maker_finalizes_deposit_tx(
        self,
        my_deposit_tx: "Transaction",
        takers_deposit_tx: "Transaction",
        num_takers_inputs: int,
    ) -> None:
        raise RuntimeError(
            "TradeWalletService.seller_as_maker_finalizes_deposit_tx Not implemented yet"
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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delayed payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

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

        WalletService.check_wallet_consistency(self._wallet)
        assert (
            input.connected_output is not None
        ), "input.connected_output must not be None"
        input.verify(input.connected_output)
        return delayed_payout_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Standard payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Mediated payoutTx
    # ///////////////////////////////////////////////////////////////////////////////////////////

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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Arbitrated payoutTx
    # ///////////////////////////////////////////////////////////////////////////////////////////

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

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Emergency payoutTx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BsqSwap tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Broadcast tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def broadcast_tx(
        self,
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout_sec: Optional[int] = None,
    ) -> None:
        check_not_none(
            self._wallet_config,
            "WalletConfig must not be None at TradeWalletService.broadcast_tx",
        )
        TxBroadcaster.broadcast_tx(self._wallet, tx, callback, timeout_sec)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Misc
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_wallet_tx(self, tx_id: str) -> "Transaction":
        check_not_none(
            self._wallet,
            "Wallet must not be None at TradeWalletService.get_wallet_tx",
        )
        return self._wallet.get_transaction(tx_id)

    def commit_tx(self, tx: "Transaction") -> None:
        check_not_none(
            self._wallet,
            "Wallet must not be None at TradeWalletService.commit_tx",
        )
        self._wallet.maybe_add_transaction(tx)

    def get_cloned_transaction(self, tx: "Transaction") -> "Transaction":
        return Transaction(self.params, tx.bitcoin_serialize())

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

    # BISQ issue #4039: prevent dust outputs from being created.
    # check all the outputs in a proposed transaction, if any are below the dust threshold
    # remove them, noting the details in the log. returns 'true' to indicate if any dust was
    # removed.
    def _remove_dust(self, transaction: "Transaction") -> bool:
        original_transaction_outputs = transaction.outputs
        keep_transaction_outputs = []

        for transaction_output in original_transaction_outputs:
            if transaction_output.get_value().is_less_than(
                Restrictions.get_min_non_dust_output()
            ):
                logger.info(
                    f"Your transaction would have contained a dust output of {transaction_output}",
                )
            else:
                keep_transaction_outputs.append(transaction_output)

        # If dust was detected, keep_transaction_outputs will have fewer elements than original_transaction_outputs
        # Set the transaction outputs to what we saved in keep_transaction_outputs, thus discarding dust.
        if len(keep_transaction_outputs) != len(original_transaction_outputs):
            logger.info(
                "Dust output was detected and removed, the new output is as follows:"
            )
            transaction.clear_outputs()
            for transaction_output in keep_transaction_outputs:
                transaction.add_output(transaction_output)
                logger.info(f"{transaction_output}")
            return True  # Dust was removed

        return False  # No action necessary
