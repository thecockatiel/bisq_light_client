from collections.abc import Callable
from typing import TYPE_CHECKING, Iterable, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.btc_coin_selector import BtcCoinSelector
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bitcoinj.base.coin import Coin
from bitcoinj.script.script_pattern import ScriptPattern
from utils.aio import FutureCallback

if TYPE_CHECKING:
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.model.address_entry_list import AddressEntryList
    from bitcoinj.core.address import Address
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.setup.wallets_setup import WalletsSetup

logger = get_logger(__name__)


# TODO
class BtcWalletService(WalletService, DaoStateListener):

    def __init__(
        self,
        wallets_setup: "WalletsSetup",
        address_entry_list: "AddressEntryList",
        preferences: "Preferences",
        fee_service: "FeeService",
    ):
        super().__init__(wallets_setup, preferences, fee_service)
        self.address_entry_list = address_entry_list

        wallets_setup.add_setup_completed_handler(self._on_setup_completed)

    def _on_setup_completed(self):
        self.wallet = self._wallets_setup.btc_wallet
        self.add_listeners_to_wallet()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Burn BSQ txs (some proposal txs, asset listing fee tx, proof of burn tx)
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def complete_prepared_burn_bsq_tx(
        self, prepared_burn_fee_tx: "Transaction", op_return_data: bytes
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_burn_bsq_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Proposal txs
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def complete_prepared_reimbursement_request_tx(
        self,
        issuance_amount: Coin,
        issuance_address: "Address",
        fee_tx: "Transaction",
        op_return_data: bytes,
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_compensation_request_tx Not implemented yet"
        )

    def complete_prepared_compensation_request_tx(
        self,
        issuance_amount: Coin,
        issuance_address: "Address",
        fee_tx: "Transaction",
        op_return_data: bytes,
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_compensation_request_tx Not implemented yet"
        )

    def _complete_prepared_proposal_tx(
        self,
        fee_tx: "Transaction",
        op_return_data: bytes,
        issuance_amount: Optional[Coin] = None,
        issuance_address: Optional["Address"] = None,
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService._complete_prepared_proposal_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Blind vote tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def complete_prepared_blind_vote_tx(
        self, prepared_tx: "Transaction", op_return_data: bytes
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_blind_vote_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Vote reveal tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def complete_prepared_vote_reveal_tx(
        self, prepared_tx: "Transaction", op_return_data: bytes
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_vote_reveal_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Add fee input to prepared BSQ send tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def complete_prepared_send_bsq_tx(
        self, prepared_bsq_tx: "Transaction", tx_fee_per_vbyte: Coin = None
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_send_bsq_tx Not implemented yet"
        )

    def complete_prepared_bsq_tx(
        self,
        prepared_bsq_tx: "Transaction",
        op_return_data: Optional[bytes],
        tx_fee_per_vbyte: Coin = None,
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.complete_prepared_bsq_tx Not implemented yet"
        )

    # // BISQ issue #4039: Prevent dust outputs from being created.
    # // Check the outputs of a proposed transaction.  If any are below the dust threshold,
    # // add up the dust, log the details, and return the cumulative dust amount.
    def get_dust(self, proposed_transaction: "Transaction") -> Coin:
        dust = Coin.ZERO()
        for transaction_output in proposed_transaction.outputs:
            if transaction_output.get_value().is_less_than(
                Restrictions.get_min_non_dust_output()
            ):
                dust = dust.add(transaction_output.get_value())
                logger.info(f"Dust TXO = {transaction_output}")
        return dust

    def get_tx_from_serialized_tx(self, serialized_tx: bytes) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.get_tx_from_serialized_tx Not implemented yet"
        )

    def get_available_address_entries(self) -> list["AddressEntry"]:
        raise RuntimeError(
            "BtcWalletService.get_available_address_entries Not implemented yet"
        )

    def get_num_inputs(self, tx: "Transaction") -> tuple[int, int]:
        num_legacy_inputs = 0
        num_segwit_inputs = 0
        for tx_input in tx.inputs:
            connected_output = tx_input.connected_output
            if (
                connected_output is None
                or ScriptPattern.is_p2pkh(connected_output.get_script_pub_key())
                or ScriptPattern.is_p2pk(connected_output.get_script_pub_key())
            ):
                # If connected_output is null, we don't know the input type. To avoid underpaying fees,
                # we treat it as a legacy input which will result in a higher fee estimation.
                num_legacy_inputs += 1
            elif ScriptPattern.is_p2wpkh(connected_output.get_script_pub_key()):
                num_segwit_inputs += 1
            else:
                raise IllegalArgumentException(
                    "Inputs should spend a P2PKH, P2PK or P2WPKH output"
                )
        return num_legacy_inputs, num_segwit_inputs

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Commit tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def commit_tx(self, tx: "Transaction") -> None:
        self.wallet.maybe_add_transaction(tx)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // AddressEntry
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_address_entry(
        self, offer_id: str, context: "AddressEntryContext"
    ) -> Optional["AddressEntry"]:
        address_list = self.get_address_entry_list_as_immutable_list()
        return next(
            (
                entry
                for entry in address_list
                if offer_id == entry.offer_id and context == entry.context
            ),
            None,
        )

    def get_or_clone_address_entry_with_offer_id(
        self, source_address_entry: "AddressEntry", offer_id: str
    ) -> "AddressEntry":
        raise RuntimeError(
            "BtcWalletService.get_or_clone_address_entry_with_offer_id Not implemented yet"
        )

    def get_or_create_address_entry(
        self, offer_id: str, context: AddressEntryContext
    ) -> "AddressEntry":
        # TODO: There's an override, check and name properly
        raise RuntimeError(
            "BtcWalletService.get_or_create_address_entry Not implemented yet"
        )

    def get_arbitrator_address_entry(self) -> "AddressEntry":
        raise RuntimeError(
            "BtcWalletService.get_arbitrator_address_entry Not implemented yet"
        )

    def get_fresh_address_entry(self) -> "AddressEntry":
        # we only support segwit addresses in python client
        raise RuntimeError(
            "BtcWalletService.get_fresh_address_entry Not implemented yet"
        )

    def recover_address_entry(
        self, offer_id: str, address: str, context: AddressEntryContext
    ) -> None:
        raise RuntimeError("BtcWalletService.recover_address_entry Not implemented yet")

    def get_estimated_fee_tx_vsize(
        self, output_values: list[Coin], tx_fee: Coin
    ) -> int:
        raise RuntimeError(
            "BtcWalletService.get_estimated_fee_tx_vsize Not implemented yet"
        )

    def get_address_entries_for_trade(self):
        return [
            entry
            for entry in self.get_address_entry_list_as_immutable_list()
            if entry.context == AddressEntryContext.MULTI_SIG
            or entry.context == AddressEntryContext.TRADE_PAYOUT
        ]

    def get_address_entries(self, context: AddressEntryContext) -> list["AddressEntry"]:
        raise RuntimeError("BtcWalletService.get_address_entries Not implemented yet")

    def get_funded_available_address_entries(self) -> list["AddressEntry"]:
        return [
            entry
            for entry in self.get_available_address_entries()
            if self.get_balance_for_address(entry.get_address()).is_positive()
        ]

    def get_address_entry_list_as_immutable_list(self) -> list["AddressEntry"]:
        raise RuntimeError(
            "BtcWalletService.get_address_entry_list_as_immutable_list Not implemented yet"
        )

    def swap_trade_entry_to_available_entry(
        self, offer_id: str, context: AddressEntryContext
    ) -> None:
        raise RuntimeError(
            "BtcWalletService.swap_trade_entry_to_available_entry Not implemented yet"
        )

    def reset_coin_locked_in_multi_sig_address_entry(self, offer_id: str) -> None:
        raise RuntimeError(
            "BtcWalletService.reset_coin_locked_in_multi_sig_address_entry Not implemented yet"
        )

    def reset_address_entries_for_open_offer(self) -> None:
        raise RuntimeError(
            "BtcWalletService.reset_address_entries_for_open_offer Not implemented yet"
        )

    def reset_address_entries_for_pending_trade(self, offer_id: str) -> None:
        raise RuntimeError(
            "BtcWalletService.reset_address_entries_for_pending_trade Not implemented yet"
        )

    def get_address_entries_for_open_offer(self) -> list[AddressEntry]:
        raise RuntimeError(
            "BtcWalletService.get_address_entries_for_open_offer Not implemented yet"
        )

    def is_unconfirmed_transactions_limit_hit(self) -> bool:
        raise RuntimeError(
            "BtcWalletService.is_unconfirmed_transactions_limit_hit Not implemented yet"
        )

    def get_multi_sig_key_pair(
        self, trade_id: str, pub_key: bytes
    ) -> "DeterministicKey":
        raise RuntimeError(
            "BtcWalletService.get_multi_sig_key_pair Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Balance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_saving_wallet_balance(self):
        return Coin.value_of(
            sum(
                self.get_balance_for_address(entry.get_address()).value
                for entry in self.get_funded_available_address_entries()
            )
        )

    def get_address_entries_for_available_balance_stream(
        self,
    ) -> Iterable[AddressEntry]:
        raise RuntimeError(
            "BtcWalletService.get_address_entries_for_available_balance_stream Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Double spend unconfirmed transaction (unlock in case we got into a tx with a too low mining fee)
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Find inputs and change
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_inputs_and_change(
        required: Coin,
    ) -> tuple[list["RawTransactionInput"], Coin]:
        raise RuntimeError("BtcWalletService.get_inputs_and_change Not implemented yet")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Withdrawal Fee calculation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_fee_estimation_transaction_for_multiple_addresses(
        self,
        from_addresses: set[str],
        to_address: str,
        amount: Coin,
        tx_fee_for_withdrawal_per_vbyte: Coin,
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.get_fee_estimation_transaction_for_multiple_addresses Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Withdrawal Send
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_funds(
        self,
        from_address: str,
        to_address: str,
        receiver_amount: Coin,
        fee: Coin,
        aes_key: Optional[bytes],
        context: AddressEntryContext,
        memo: Optional[str],
        callback: FutureCallback["Transaction"],
    ) -> str:
        raise RuntimeError("BtcWalletService.send_funds Not implemented yet")

    def send_funds_for_multiple_addresses(
        self,
        from_addresses: set[str],
        to_address: str,
        receiver_amount: Coin,
        fee: Coin,
        change_address: Optional[str],
        aes_key: Optional[bytes],
        memo: Optional[str],
        callback: FutureCallback["Transaction"],
    ) -> "Transaction":
        raise RuntimeError(
            "BtcWalletService.send_funds_for_multiple_addresses Not implemented yet"
        )
