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
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.script.script_builder import ScriptBuilder
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.wallet.send_request import SendRequest
from utils.aio import FutureCallback
from utils.preconditions import check_argument

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
        return self._complete_prepared_proposal_tx(
            prepared_burn_fee_tx,
            op_return_data,
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
        return self._complete_prepared_proposal_tx(
            fee_tx, op_return_data, issuance_amount, issuance_address
        )

    def complete_prepared_compensation_request_tx(
        self,
        issuance_amount: Coin,
        issuance_address: "Address",
        fee_tx: "Transaction",
        op_return_data: bytes,
    ) -> "Transaction":
        return self._complete_prepared_proposal_tx(
            fee_tx, op_return_data, issuance_amount, issuance_address
        )

    def _complete_prepared_proposal_tx(
        self,
        fee_tx: "Transaction",
        op_return_data: bytes,
        issuance_amount: Optional[Coin] = None,
        issuance_address: Optional["Address"] = None,
    ) -> "Transaction":
        # (BsqFee)tx has following structure:
        # inputs [1-n] BSQ inputs (fee)
        # outputs [0-1] BSQ request fee change output (>= 546 Satoshi)

        # preparedCompensationRequestTx has following structure:
        # inputs [1-n] BSQ inputs for request fee
        # inputs [1-n] BTC inputs for BSQ issuance and miner fee
        # outputs [1] Mandatory BSQ request fee change output (>= 546 Satoshi)
        # outputs [1] Potentially BSQ issuance output (>= 546 Satoshi) - in case of a issuance tx, otherwise that output does not exist
        # outputs [0-1] BTC change output from issuance and miner fee inputs (>= 546 Satoshi)
        # outputs [1] OP_RETURN with opReturnData and amount 0
        # mining fee: BTC mining fee + burned BSQ fee

        prepared_tx = Transaction(self.params)
        # Copy inputs from BSQ fee tx
        for tx_input in fee_tx.inputs:
            prepared_tx.add_input(tx_input)

        # Need to be first because issuance is not guaranteed to be valid and would otherwise burn change output!
        # BSQ change outputs from BSQ fee inputs.
        for tx_output in fee_tx.outputs:
            prepared_tx.add_output(tx_output)

        # For generic proposals there is no issuance output, for compensation and reimburse requests there is
        if issuance_amount is not None and issuance_address is not None:
            # BSQ issuance output
            prepared_tx.add_output_using_coin_and_address(
                issuance_amount, issuance_address
            )

        # safety check counter to avoid endless loops
        counter = 0
        # estimated size of input sig
        sig_size_per_input = 106
        # typical size for a tx with 3 inputs
        tx_vsize_with_unsigned_inputs = 300
        tx_fee_per_vbyte = self._fee_service.get_tx_fee_per_vbyte()

        change_address = self.get_fresh_address_entry().get_address()
        assert change_address is not None, "change_address must not be None"

        coin_selector = BtcCoinSelector(
            self._wallets_setup.get_addresses_by_context(AddressEntryContext.AVAILABLE),
            self._preferences.get_ignore_dust_threshold(),
        )
        prepared_bsq_tx_inputs = list(prepared_tx.inputs)
        prepared_bsq_tx_outputs = list(prepared_tx.outputs)

        num_legacy_inputs, num_segwit_inputs = self.get_num_inputs(prepared_tx)
        result_tx: "Transaction" = None
        is_fee_outside_tolerance = True

        while is_fee_outside_tolerance:
            counter += 1
            if counter >= 10:
                assert result_tx is not None, "result_tx should not be None"
                logger.error(f"Could not calculate the fee. Tx={result_tx}")
                break

            tx = Transaction(self.params)
            for tx_input in prepared_bsq_tx_inputs:
                tx.add_input(tx_input)
            for tx_output in prepared_bsq_tx_outputs:
                tx.add_output(tx_output)

            send_request = SendRequest.for_tx(tx)
            send_request.shuffle_outputs = False
            send_request.password = self.password
            # signInputs needs to be false as it would try to sign all inputs (BSQ inputs are not in this wallet)
            send_request.sign_inputs = False

            send_request.fee = tx_fee_per_vbyte.multiply(
                tx_vsize_with_unsigned_inputs
                + sig_size_per_input * num_legacy_inputs
                + sig_size_per_input * num_segwit_inputs // 4
            )
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False

            send_request.coin_selector = coin_selector
            send_request.change_address = change_address
            self.wallet.complete_tx(send_request)

            result_tx = send_request.tx

            # add OP_RETURN output
            result_tx.add_output(
                TransactionOutput.from_coin_and_script(
                    Coin.ZERO(),
                    ScriptBuilder.create_op_return_script(op_return_data).program,
                    tx,
                )
            )

            num_legacy_inputs, num_segwit_inputs = self.get_num_inputs(result_tx)
            tx_vsize_with_unsigned_inputs = result_tx.get_vsize()
            estimated_fee = tx_fee_per_vbyte.multiply(
                tx_vsize_with_unsigned_inputs
                + sig_size_per_input * num_legacy_inputs
                + sig_size_per_input * num_segwit_inputs // 4
            ).value

            # calculated fee must be inside of a tolerance range with tx fee
            is_fee_outside_tolerance = (
                abs(result_tx.get_fee().value - estimated_fee) > 1000
            )

        # Sign all BTC inputs
        # TODO: Check if this is correct
        result_tx = self.wallet.sign_tx(self.password, result_tx)

        WalletService.check_wallet_consistency(self.wallet)
        WalletService.verify_transaction(result_tx)

        # self.print_tx("BTC wallet: Signed Tx", result_tx)
        return result_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Blind vote tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We add BTC inputs to pay miner fees and sign the BTC tx inputs

    # (BsqFee)tx has following structure:
    # inputs [1-n] BSQ inputs (fee + stake)
    # outputs [1] BSQ stake
    # outputs [0-1] BSQ change output (>= 546 Satoshi)

    # preparedVoteTx has following structure:
    # inputs [1-n] BSQ inputs (fee + stake)
    # inputs [1-n] BTC inputs for miner fee
    # outputs [1] BSQ stake
    # outputs [0-1] BSQ change output (>= 546 Satoshi)
    # outputs [0-1] BTC change output from miner fee inputs (>= 546 Satoshi)
    # outputs [1] OP_RETURN with opReturnData and amount 0
    # mining fee: BTC mining fee + burned BSQ fee
    def complete_prepared_blind_vote_tx(
        self, prepared_tx: "Transaction", op_return_data: bytes
    ) -> "Transaction":
        # First input index for btc inputs (they get added after bsq inputs)
        return self._complete_prepared_bsq_tx_with_btc_fee(prepared_tx, op_return_data)

    def _complete_prepared_bsq_tx_with_btc_fee(
        self, prepared_tx: "Transaction", op_return_data: bytes
    ) -> "Transaction":
        tx = self._add_inputs_for_miner_fee(prepared_tx, op_return_data)
        # Sign all BTC inputs
        # TODO: Check if this is correct
        tx = self.wallet.sign_tx(self.password, tx)

        WalletService.check_wallet_consistency(self.wallet)
        WalletService.verify_transaction(tx)

        # self.print_tx("BTC wallet: Signed tx", tx)
        return tx

    def _add_inputs_for_miner_fee(
        self, prepared_tx: "Transaction", op_return_data: bytes
    ):
        # safety check counter to avoid endless loops
        counter = 0
        # estimated size of input sig
        sig_size_per_input = 106
        # typical size for a tx with 3 inputs
        tx_vsize_with_unsigned_inputs = 300
        tx_fee_per_vbyte = self._fee_service.get_tx_fee_per_vbyte()

        change_address = self.get_fresh_address_entry().get_address()
        assert change_address is not None, "change_address must not be None"

        coin_selector = BtcCoinSelector(
            self._wallets_setup.get_addresses_by_context(AddressEntryContext.AVAILABLE),
            self._preferences.get_ignore_dust_threshold(),
        )
        prepared_bsq_tx_inputs = list(prepared_tx.inputs)
        prepared_bsq_tx_outputs = list(prepared_tx.outputs)

        num_legacy_inputs, num_segwit_inputs = self.get_num_inputs(prepared_tx)
        result_tx: "Transaction" = None
        is_fee_outside_tolerance = True

        while is_fee_outside_tolerance:
            counter += 1
            if counter >= 10:
                assert result_tx is not None, "result_tx should not be None"
                logger.error(f"Could not calculate the fee. Tx={result_tx}")
                break

            tx = Transaction(self.params)
            for tx_input in prepared_bsq_tx_inputs:
                tx.add_input(tx_input)
            for tx_output in prepared_bsq_tx_outputs:
                tx.add_output(tx_output)

            send_request = SendRequest.for_tx(tx)
            send_request.shuffle_outputs = False
            send_request.password = self.password
            # signInputs needs to be false as it would try to sign all inputs (BSQ inputs are not in this wallet)
            send_request.sign_inputs = False

            send_request.fee = tx_fee_per_vbyte.multiply(
                tx_vsize_with_unsigned_inputs
                + sig_size_per_input * num_legacy_inputs
                + sig_size_per_input * num_segwit_inputs // 4
            )
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False

            send_request.coin_selector = coin_selector
            send_request.change_address = change_address
            self.wallet.complete_tx(send_request)

            result_tx = send_request.tx

            # add OP_RETURN output
            result_tx.add_output(
                TransactionOutput.from_coin_and_script(
                    Coin.ZERO(),
                    ScriptBuilder.create_op_return_script(op_return_data).program,
                    tx,
                )
            )

            num_legacy_inputs, num_segwit_inputs = self.get_num_inputs(result_tx)
            tx_vsize_with_unsigned_inputs = result_tx.get_vsize()
            estimated_fee = tx_fee_per_vbyte.multiply(
                tx_vsize_with_unsigned_inputs
                + sig_size_per_input * num_legacy_inputs
                + sig_size_per_input * num_segwit_inputs // 4
            ).value

            # calculated fee must be inside of a tolerance range with tx fee
            is_fee_outside_tolerance = (
                abs(result_tx.get_fee().value - estimated_fee) > 1000
            )

        return result_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Vote reveal tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We add BTC fees to the prepared reveal tx
    # (BsqFee)tx has following structure:
    # inputs [1] BSQ input (stake)
    # output [1] BSQ unlocked stake

    # preparedVoteTx has following structure:
    # inputs [1] BSQ inputs (stake)
    # inputs [1-n] BTC inputs for miner fee
    # outputs [1] BSQ unlocked stake
    # outputs [0-1] BTC change output from miner fee inputs (>= 546 Satoshi)
    # outputs [1] OP_RETURN with opReturnData and amount 0
    # mining fee: BTC mining fee + burned BSQ fee
    def complete_prepared_vote_reveal_tx(
        self, prepared_tx: "Transaction", op_return_data: bytes
    ) -> "Transaction":
        return self._complete_prepared_bsq_tx_with_btc_fee(prepared_tx, op_return_data)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Add fee input to prepared BSQ send tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def complete_prepared_send_bsq_tx(
        self, prepared_bsq_tx: "Transaction", tx_fee_per_vbyte: Coin = None
    ) -> "Transaction":
        # preparedBsqTx has following structure:
        # inputs [1-n] BSQ inputs
        # outputs [1] BSQ receiver's output
        # outputs [0-1] BSQ change output

        # We add BTC mining fee. Result tx looks like:
        # inputs [1-n] BSQ inputs
        # inputs [1-n] BTC inputs
        # outputs [1] BSQ receiver's output
        # outputs [0-1] BSQ change output
        # outputs [0-1] BTC change output
        # mining fee: BTC mining fee
        if tx_fee_per_vbyte is None:
            tx_fee_per_vbyte = self.get_tx_fee_for_withdrawal_per_vbyte()
        return self.complete_prepared_bsq_tx(prepared_bsq_tx, None, tx_fee_per_vbyte)

    def complete_prepared_bsq_tx(
        self,
        prepared_bsq_tx: "Transaction",
        op_return_data: Optional[bytes],
        tx_fee_per_vbyte: Coin = None,
    ) -> "Transaction":
        if tx_fee_per_vbyte is None:
            tx_fee_per_vbyte = self.get_tx_fee_for_withdrawal_per_vbyte()

        # preparedBsqTx has following structure:
        # inputs [1-n] BSQ inputs
        # outputs [1] BSQ receiver's output
        # outputs [0-1] BSQ change output
        # mining fee: optional burned BSQ fee (only if opReturnData != null)

        # We add BTC mining fee. Result tx looks like:
        # inputs [1-n] BSQ inputs
        # inputs [1-n] BTC inputs
        # outputs [0-1] BSQ receiver's output
        # outputs [0-1] BSQ change output
        # outputs [0-1] BTC change output
        # outputs [0-1] OP_RETURN with opReturnData (only if opReturnData != null)
        # mining fee: BTC mining fee + optional burned BSQ fee (only if opReturnData != null)

        # In case of txs for burned BSQ fees we have no receiver output and it might be that there is no change outputs
        # We need to guarantee that min. 1 valid output is added (OP_RETURN does not count). So we use a higher input
        # for BTC to force an additional change output.

        # safety check counter to avoid endless loops
        counter = 0
        # estimated size of input sig
        sig_size_per_input = 106
        # typical size for a tx with 2 inputs
        tx_vsize_with_unsigned_inputs = 203
        # In case there are no change outputs we force a change by adding min dust to the BTC input
        forced_change_value = Coin.ZERO()

        change_address = self.get_fresh_address_entry().get_address()
        assert change_address is not None, "change_address must not be None"

        coin_selector = BtcCoinSelector(
            self._wallets_setup.get_addresses_by_context(AddressEntryContext.AVAILABLE),
            self._preferences.get_ignore_dust_threshold(),
        )
        prepared_bsq_tx_inputs = list(prepared_bsq_tx.inputs)
        prepared_bsq_tx_outputs = list(prepared_bsq_tx.outputs)

        # We don't know at this point what type the btc input would be (segwit/legacy).
        # We use legacy to be on the safe side.
        num_legacy_inputs = len(prepared_bsq_tx_inputs)
        num_segwit_inputs = 0
        result_tx: "Transaction" = None
        is_fee_outside_tolerance = True
        op_return_is_only_output = True

        while (
            is_fee_outside_tolerance
            or op_return_is_only_output
            or (
                result_tx.get_fee().value
                < tx_fee_per_vbyte.multiply(result_tx.get_vsize()).value
            )
        ):
            counter += 1
            if counter >= 10:
                assert result_tx is not None, "result_tx should not be None"
                logger.error(f"Could not calculate the fee. Tx={result_tx}")
                break

            tx = Transaction(self.params)
            for tx_input in prepared_bsq_tx_inputs:
                tx.add_input(tx_input)

            if forced_change_value.is_zero():
                for tx_output in prepared_bsq_tx_outputs:
                    tx.add_output(tx_output)
            else:
                # JAVA TODO test that case
                check_argument(
                    len(prepared_bsq_tx_outputs) == 0,
                    "prepared_bsq_tx_outputs size must be 0 in that code branch",
                )
                tx.add_output_using_coin_and_address(
                    forced_change_value, change_address
                )

            send_request = SendRequest.for_tx(tx)
            send_request.shuffle_outputs = False
            send_request.password = self.password
            # signInputs needs to be false as it would try to sign all inputs (BSQ inputs are not in this wallet)
            send_request.sign_inputs = False

            send_request.fee = tx_fee_per_vbyte.multiply(
                tx_vsize_with_unsigned_inputs
                + sig_size_per_input * num_legacy_inputs
                + sig_size_per_input * num_segwit_inputs // 4
            )
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False

            send_request.coin_selector = coin_selector
            send_request.change_address = change_address
            self.wallet.complete_tx(send_request)

            result_tx = send_request.tx

            # We might have the rare case that both inputs matched the required fees, so both did not require
            # a change output.
            # In such cases we need to add artificially a change output (OP_RETURN is not allowed as only output)
            op_return_is_only_output = (
                len(result_tx._electrum_transaction._outputs) == 0
            )
            forced_change_value = (
                Restrictions.get_min_non_dust_output()
                if op_return_is_only_output
                else Coin.ZERO()
            )

            # add OP_RETURN output
            if op_return_data is not None:
                result_tx.add_output(
                    TransactionOutput.from_coin_and_script(
                        Coin.ZERO(),
                        ScriptBuilder.create_op_return_script(op_return_data).program,
                        tx,
                    )
                )

            num_legacy_inputs, num_segwit_inputs = self.get_num_inputs(result_tx)
            tx_vsize_with_unsigned_inputs = result_tx.get_vsize()
            estimated_fee = tx_fee_per_vbyte.multiply(
                tx_vsize_with_unsigned_inputs
                + sig_size_per_input * num_legacy_inputs
                + sig_size_per_input * num_segwit_inputs // 4
            ).value

            # calculated fee must be inside of a tolerance range with tx fee
            is_fee_outside_tolerance = (
                abs(result_tx.get_fee().value - estimated_fee) > 1000
            )

        # Sign all BTC inputs
        # TODO: Check if this is correct
        result_tx = self.wallet.sign_tx(self.password, result_tx)

        WalletService.check_wallet_consistency(self.wallet)
        WalletService.verify_transaction(result_tx)

        self.print_tx("BTC wallet: Signed tx", result_tx)
        return result_tx

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

    def get_available_address_entries(self) -> list["AddressEntry"]:
        return [
            address_entry
            for address_entry in self.get_address_entry_list_as_immutable_list()
            if address_entry.context == AddressEntryContext.AVAILABLE
        ]

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
