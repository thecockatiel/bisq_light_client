from collections.abc import Callable
import itertools
from typing import TYPE_CHECKING, Iterable, Optional
from bisq.common.crypto.encryption import ECPrivkey
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.exceptions.address_entry_exception import AddressEntryException
from bisq.core.btc.exceptions.insufficient_funds_exception import (
    InsufficientFundsException,
)
from bisq.core.btc.model.address_entry import AddressEntry
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.btc_coin_selector import BtcCoinSelector
from bisq.core.btc.wallet.http.mem_pool_space_tx_broadcaster import (
    MemPoolSpaceTxBroadcaster,
)
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.script.script_builder import ScriptBuilder
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.script.script_type import ScriptType
from bitcoinj.wallet.send_request import SendRequest
from utils.aio import FutureCallback
from utils.preconditions import check_argument, check_not_none, check_state
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.address import Address


if TYPE_CHECKING:
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.model.address_entry_list import AddressEntryList
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bitcoinj.crypto.deterministic_key import DeterministicKey
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
        index_of_btc_first_input = len(fee_tx.inputs)

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
        result_tx = self._sign_all_btc_inputs(index_of_btc_first_input, result_tx)

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
        # Remember index for first BTC input
        index_of_btc_first_input = len(prepared_tx.inputs)

        tx = self._add_inputs_for_miner_fee(prepared_tx, op_return_data)
        tx = self._sign_all_btc_inputs(index_of_btc_first_input, tx)

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

    def _sign_all_btc_inputs(
        self, index_of_btc_first_input: int, tx: "Transaction"
    ) -> None:
        # TODO: Check if this works correctly
        tx = check_not_none(
            self.wallet.sign_tx(self.password, tx),
            "failed to sign tx at sign_all_btc_inputs",
        )
        for i in range(index_of_btc_first_input, len(tx.inputs)):
            tx_input = tx.inputs[i]
            connected_output = tx_input.connected_output
            check_argument(
                connected_output is not None
                and connected_output.is_for_wallet(self.wallet),
                "tx_input.connected_output is not in our wallet. That must not happen.",
            )
            self.check_script_sig(tx, tx_input, i)
        return tx

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
        result_tx = self._sign_all_btc_inputs(len(prepared_bsq_tx_inputs), result_tx)

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

    # For cloned offers with shared maker fee we create a new address entry based on the source entry
    # and set the new offerId.
    def get_or_clone_address_entry_with_offer_id(
        self, source_address_entry: "AddressEntry", offer_id: str
    ) -> "AddressEntry":
        address_entry = next(
            (
                entry
                for entry in self.get_address_entry_list_as_immutable_list()
                if offer_id == entry.offer_id
                and source_address_entry.context == entry.context
            ),
            None,
        )
        if address_entry:
            return address_entry
        else:
            clone_with_new_offer_id = AddressEntry(
                source_address_entry.key_pair,
                source_address_entry.context,
                offer_id,
                segwit=source_address_entry.segwit,
            )
            self.address_entry_list.add_address_entry(clone_with_new_offer_id)
            return clone_with_new_offer_id

    def get_or_create_address_entry(
        self, offer_id: str, context: AddressEntryContext
    ) -> "AddressEntry":
        address_entry = next(
            (
                entry
                for entry in self.get_address_entry_list_as_immutable_list()
                if offer_id == entry.offer_id and context == entry.context
            ),
            None,
        )
        if address_entry:
            return address_entry
        else:
            #  We try to use available and not yet used entries
            empty_available_address_entry = next(
                (
                    entry
                    for entry in self.get_address_entry_list_as_immutable_list()
                    if entry.context == AddressEntryContext.AVAILABLE
                    and (addr := entry.get_address())
                    and self.is_address_unused(addr)
                    and addr.output_script_type == ScriptType.P2WPKH
                ),
                None,
            )
            if (
                empty_available_address_entry
                and context != AddressEntryContext.MULTI_SIG
            ):
                return self.address_entry_list.swap_available_to_address_entry_with_offer_id(
                    empty_available_address_entry, context, offer_id
                )
            else:
                key = self.wallet.find_key_from_address(
                    self.wallet.get_receiving_address()
                )
                entry = AddressEntry(key, context, offer_id, segwit=True)
                logger.info(f"get_or_create_address_entry: new AddressEntry={entry}")
                self.address_entry_list.add_address_entry(entry)
                return entry

    def get_available_address_entries(self) -> list["AddressEntry"]:
        return [
            address_entry
            for address_entry in self.get_address_entry_list_as_immutable_list()
            if address_entry.context == AddressEntryContext.AVAILABLE
        ]

    def get_arbitrator_address_entry(self) -> "AddressEntry":
        address_entry = next(
            (
                e
                for e in self.get_address_entry_list_as_immutable_list()
                if e.context == AddressEntryContext.ARBITRATOR
            ),
            None,
        )
        return self.get_or_create_address_entry_segwit(
            AddressEntryContext.ARBITRATOR, address_entry
        )

    def get_fresh_address_entry(self) -> "AddressEntry":
        # we only support segwit addresses in python client
        available_address_entry = next(
            (
                entry
                for entry in self.get_address_entry_list_as_immutable_list()
                if entry.context == AddressEntryContext.AVAILABLE
                and self.is_address_unused(entry.get_address())
                and entry.get_address().output_script_type == ScriptType.P2WPKH
            ),
            None,
        )
        return self.get_or_create_address_entry_segwit(
            AddressEntryContext.AVAILABLE, available_address_entry
        )

    def recover_address_entry(
        self, offer_id: str, address: str, context: AddressEntryContext
    ) -> None:
        address_entry = self._find_address_entry(address, context)
        if address_entry:
            self.address_entry_list.swap_available_to_address_entry_with_offer_id(
                address_entry, context, offer_id
            )

    def get_or_create_address_entry_segwit(
        self, context: AddressEntryContext, address_entry: Optional["AddressEntry"]
    ) -> "AddressEntry":
        if address_entry:
            return address_entry
        else:
            # NOTE: we only use segwit
            key = self.wallet.find_key_from_address(self.wallet.get_receiving_address())
            entry = AddressEntry(key, context, segwit=True)
            logger.info(
                f"get_or_create_address_entry_with_context: add new AddressEntry {entry}"
            )
            self.address_entry_list.add_address_entry(entry)
            return entry

    def _find_address_entry(self, address: str, context: "AddressEntryContext"):
        return next(
            (
                entry
                for entry in self.get_address_entry_list_as_immutable_list()
                if address == entry.get_address_string() and context == entry.context
            ),
            None,
        )

    def get_address_entries_for_trade(self):
        return [
            entry
            for entry in self.get_address_entry_list_as_immutable_list()
            if entry.context == AddressEntryContext.MULTI_SIG
            or entry.context == AddressEntryContext.TRADE_PAYOUT
        ]

    def get_address_entries(
        self, context: "AddressEntryContext"
    ) -> list["AddressEntry"]:
        return [
            address_entry
            for address_entry in self.get_address_entry_list_as_immutable_list()
            if context == address_entry.context
        ]

    def get_funded_available_address_entries(self) -> list["AddressEntry"]:
        return [
            entry
            for entry in self.get_available_address_entries()
            if self.get_balance_for_address(entry.get_address()).is_positive()
        ]

    def get_address_entry_list_as_immutable_list(self) -> list["AddressEntry"]:
        return self.address_entry_list.entry_set.copy()

    def swap_trade_entry_to_available_entry(
        self, offer_id: str, context: AddressEntryContext
    ) -> None:
        if context == AddressEntryContext.MULTI_SIG:
            logger.error(
                "swap_trade_entry_to_available_entry called with MULTI_SIG context. "
                "This is not permitted as we must not reuse those address entries and there "
                "are no redeemable funds on those addresses. Only the keys are used for creating "
                f"the Multisig address. offer_id={offer_id}, context={context}"
            )
            return

        for entry in self.get_address_entry_list_as_immutable_list():
            if offer_id == entry.offer_id and context == entry.context:
                logger.info(
                    f"swap addressEntry with address {entry.get_address_string()} and offerId {entry.offer_id} from context {context} to available"
                )
                self.address_entry_list.swap_to_available(entry)

    # When funds from MultiSig address is spent we reset the coinLockedInMultiSig value to 0.
    def reset_coin_locked_in_multi_sig_address_entry(self, offer_id: str) -> None:
        self.set_coin_locked_in_multi_sig_address_entry_for_offer_id(offer_id, 0)

    def set_coin_locked_in_multi_sig_address_entry_for_offer_id(
        self, offer_id: str, value: int
    ) -> None:
        for address_entry in self.get_address_entry_list_as_immutable_list():
            if (
                address_entry.context == AddressEntryContext.MULTI_SIG
                and address_entry.offer_id == offer_id
            ):
                self.set_coin_locked_in_multi_sig_address_entry(address_entry, value)

    def set_coin_locked_in_multi_sig_address_entry(
        self, address_entry: "AddressEntry", value: int
    ) -> None:
        logger.info(
            f"Set coinLockedInMultiSig for addressEntry {address_entry} to value {value}"
        )
        self.address_entry_list.set_coin_locked_in_multi_sig_address_entry(
            address_entry, value
        )

    def reset_address_entries_for_open_offer(self, offer_id: str) -> None:
        logger.info(f"reset_address_entries_for_open_offer offerId={offer_id}")
        self.swap_trade_entry_to_available_entry(
            offer_id, AddressEntryContext.OFFER_FUNDING
        )
        self.swap_trade_entry_to_available_entry(
            offer_id, AddressEntryContext.RESERVED_FOR_TRADE
        )

    def reset_address_entries_for_pending_trade(self, offer_id: str) -> None:
        # We must not swap MULTI_SIG entries as those addresses are not detected in the isAddressUnused
        # check at getOrCreateAddressEntry and could lead to a reuse of those keys and result in the same 2of2 MS
        # address if same peers trade again.

        # We swap TRADE_PAYOUT to be sure all is cleaned up. There might be cases where a user cannot send the funds
        # to an external wallet directly in the last step of the trade, but the funds are in the Bisq wallet anyway and
        # the dealing with the external wallet is pure UI thing. The user can move the funds to the wallet and then
        # send out the funds to the external wallet. As this cleanup is a rare situation and most users do not use
        # the feature to send out the funds we prefer that strategy (if we keep the address entry it might cause
        # complications in some edge cases after a SPV resync).
        self.swap_trade_entry_to_available_entry(
            offer_id, AddressEntryContext.TRADE_PAYOUT
        )

    def get_address_entries_for_open_offer(self) -> list[AddressEntry]:
        ctx_filter = {
            AddressEntryContext.OFFER_FUNDING,
            AddressEntryContext.RESERVED_FOR_TRADE,
        }
        return [
            address_entry
            for address_entry in self.get_address_entry_list_as_immutable_list()
            if address_entry.context in ctx_filter
        ]

    def save_address_entry_list(self):
        self.address_entry_list.request_persistence()

    def get_multi_sig_key_pair(
        self, trade_id: str, pub_key: bytes
    ) -> "DeterministicKey":
        multi_sig_key_pair = None
        multi_sig_address_entry = self.get_address_entry(
            trade_id, AddressEntryContext.MULTI_SIG
        )
        if multi_sig_address_entry:
            multi_sig_key_pair = multi_sig_address_entry.key_pair
            if pub_key != multi_sig_address_entry.pub_key:
                logger.error(
                    f"Pub Key from AddressEntry does not match key pair from trade data. Trade ID={trade_id}\n"
                    "We try to find the keypair in the wallet with the pubKey we found in the trade data."
                )
                multi_sig_key_pair = self.wallet.find_key_from_pub_key(pub_key, None)
        else:
            logger.error(
                f"multiSigAddressEntry not found for trade ID={trade_id}.\n"
                "We try to find the keypair in the wallet with the pubKey we found in the trade data."
            )
            multi_sig_key_pair = self.wallet.find_key_from_pub_key(pub_key, None)

        return multi_sig_key_pair

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
        available_and_payout = itertools.chain(
            self.get_address_entries(AddressEntryContext.TRADE_PAYOUT),
            self.get_funded_available_address_entries(),
        )
        available = itertools.chain(
            available_and_payout,
            self.get_address_entries(AddressEntryContext.ARBITRATOR),
            self.get_address_entries(AddressEntryContext.OFFER_FUNDING),
        )
        return filter(
            lambda address_entry: self.get_balance_for_address(
                address_entry.get_address()
            ).is_positive(),
            available,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Double spend unconfirmed transaction (unlock in case we got into a tx with a too low mining fee)
    # ///////////////////////////////////////////////////////////////////////////////////////////

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
        address_entries = set["AddressEntry"]()
        for address in from_addresses:
            address_entry = self._find_address_entry(
                address, AddressEntryContext.AVAILABLE
            )
            if not address_entry:
                address_entry = self._find_address_entry(
                    address, AddressEntryContext.OFFER_FUNDING
                )
            if not address_entry:
                address_entry = self._find_address_entry(
                    address, AddressEntryContext.TRADE_PAYOUT
                )
            if not address_entry:
                address_entry = self._find_address_entry(
                    address, AddressEntryContext.ARBITRATOR
                )
            if address_entry:
                address_entries.add(address_entry)

        if not address_entries:
            raise AddressEntryException("No Addresses for withdraw found in our wallet")

        try:
            fee = Coin.ZERO()
            counter = 0
            tx_vsize = 0
            tx = None
            while True:
                counter += 1
                fee = tx_fee_for_withdrawal_per_vbyte.multiply(tx_vsize)
                send_request = self._get_send_request_for_multiple_addresses(
                    from_addresses, to_address, amount, fee, None, None
                )
                self.wallet.complete_tx(send_request)
                tx = send_request.tx
                tx_vsize = tx.get_vsize()
                self.print_tx("FeeEstimationTransactionForMultipleAddresses", tx)
                if not self._tx_fee_estimation_not_satisfied(counter, tx):
                    # satisfied
                    break
                if counter == 10:
                    logger.error(f"Could not calculate the fee. Tx={tx}")
                    break
            return tx
        except InsufficientMoneyException as e:
            raise InsufficientFundsException(
                "The fees for that transaction exceed the available funds "
                "or the resulting output value is below the min. dust value:\n"
                f"Missing: {e.missing.to_friendly_string() if e.missing else 'None'}"
            )

    def _tx_fee_estimation_not_satisfied(self, counter: int, tx: "Transaction"):
        return self._fee_estimation_not_satisfied(
            counter,
            tx.get_fee().value,
            tx.get_vsize(),
            self.get_tx_fee_for_withdrawal_per_vbyte(),
        )

    def _fee_estimation_not_satisfied(
        self,
        counter: int,
        tx_fee: int,
        tx_vsize: int,
        tx_fee_for_withdrawal_per_vbyte: Coin,
    ):
        target_fee = tx_fee_for_withdrawal_per_vbyte.multiply(tx_vsize).value
        higher_than_target_fee = tx_fee - target_fee
        return counter < 10 and (tx_fee < target_fee or higher_than_target_fee > 1000)

    def get_estimated_fee_tx_vsize(
        self, output_values: list[Coin], tx_fee: Coin
    ) -> int:
        tx = Transaction(self.params)
        # In reality txs have a mix of segwit/legacy ouputs, but we don't care too much because the size of
        # a segwit ouput is just 3 byte smaller than the size of a legacy ouput.
        dummy_address = SegwitAddress.from_key(
            ECPrivkey.generate_random_key(), self.params
        )
        for output_value in output_values:
            tx.add_output(
                TransactionOutput.from_coin_and_address(output_value, dummy_address, tx)
            )
        send_request = SendRequest.for_tx(tx)
        send_request.shuffle_outputs = False
        send_request.password = None
        send_request.coin_selector = BtcCoinSelector(
            self._wallets_setup.get_addresses_by_context(AddressEntryContext.AVAILABLE),
            self._preferences.get_ignore_dust_threshold(),
        )
        send_request.fee = tx_fee
        send_request.fee_per_kb = Coin.ZERO()
        send_request.ensure_min_required_fee = False
        send_request.change_address = dummy_address
        self.wallet.complete_tx(send_request)
        tx = send_request.tx
        return tx.get_vsize()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Withdrawal Send
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def send_funds(
        self,
        from_address: str,
        to_address: str,
        receiver_amount: Coin,
        fee: Coin,
        password: Optional[str],
        context: AddressEntryContext,
        memo: Optional[str],
        callback: FutureCallback["Transaction"],
    ) -> str:
        send_request = self._get_send_request(
            from_address, to_address, receiver_amount, fee, password, context
        )
        send_request.tx.memo = memo
        future = self.wallet.send_coins(send_request)

        def on_success(_):
            callback.on_success(send_request.tx)

        def on_error(e: Exception):
            callback.on_failure(e)

        future.add_done_callback(FutureCallback(on_success, on_error))
        # For better redundancy in case the broadcast via Electrum fails we also
        # publish the tx via mempool nodes.
        # MemPoolSpaceTxBroadcaster.broadcast_tx(send_request.tx)

        return send_request.tx.get_tx_id()

    def send_funds_for_multiple_addresses(
        self,
        from_addresses: set[str],
        to_address: str,
        receiver_amount: Coin,
        fee: Coin,
        change_address: Optional[str],
        password: Optional[str],
        memo: Optional[str],
        callback: FutureCallback["Transaction"],
    ) -> "Transaction":
        send_request = self._get_send_request_for_multiple_addresses(
            from_addresses, to_address, receiver_amount, fee, change_address, password
        )
        send_request.tx.memo = memo
        future = self.wallet.send_coins(send_request)

        def on_success(_):
            callback.on_success(send_request.tx)

        def on_error(e: Exception):
            callback.on_failure(e)

        future.add_done_callback(FutureCallback(on_success, on_error))

        self.print_tx("sendFunds", send_request.tx)

        # For better redundancy in case the broadcast via Electrum fails we also
        # publish the tx via mempool nodes.
        # MemPoolSpaceTxBroadcaster.broadcast_tx(send_request.tx)

        return send_request.tx

    def _get_send_request(
        self,
        from_address: str,
        to_address: str,
        amount: Coin,
        fee: Coin,
        password: Optional[str],
        context: AddressEntryContext,
    ) -> "SendRequest":
        tx = Transaction(self.params)
        receiver_amount = amount.subtract(fee)
        check_argument(
            Restrictions.is_above_dust(receiver_amount),
            "The amount is too low (dust limit).",
        )
        tx.add_output(
            TransactionOutput.from_coin_and_address(
                receiver_amount, Address.from_string(to_address, self.params), tx
            )
        )

        send_request = SendRequest.for_tx(tx)
        send_request.fee = fee
        send_request.fee_per_kb = Coin.ZERO()
        send_request.ensure_min_required_fee = False
        send_request.password = password
        send_request.shuffle_outputs = False

        address_entry = self._find_address_entry(from_address, context)
        if not address_entry:
            raise AddressEntryException(
                "WithdrawFromAddress is not found in our wallet."
            )

        check_argument(address_entry is not None, "address_entry must not be None")
        check_argument(
            address_entry.get_address() is not None,
            "address_entry.get_address() must not be None",
        )
        send_request.coin_selector = BtcCoinSelector(
            address_entry.get_address(), self._preferences.get_ignore_dust_threshold()
        )
        send_request.change_address = address_entry.get_address()
        return send_request

    def _get_send_request_for_multiple_addresses(
        self,
        from_addresses: set[str],
        to_address: str,
        amount: Coin,
        fee: Coin,
        change_address: Optional[str],
        password: Optional[str],
    ) -> "SendRequest":
        tx = Transaction(self.params)
        net_value = amount.subtract(fee)
        check_argument(
            Restrictions.is_above_dust(net_value), "The amount is too low (dust limit)."
        )

        tx.add_output(
            TransactionOutput.from_coin_and_address(
                net_value, Address.from_string(to_address, self.params), tx
            )
        )

        send_request = SendRequest.for_tx(tx)
        send_request.fee = fee
        send_request.fee_per_kb = Coin.ZERO()
        send_request.ensure_min_required_fee = False
        send_request.password = password
        send_request.shuffle_outputs = False

        address_entries = set["AddressEntry"]()
        for address in from_addresses:
            address_entry = self._find_address_entry(
                address, AddressEntryContext.AVAILABLE
            )
            if not address_entry:
                address_entry = self._find_address_entry(
                    address, AddressEntryContext.OFFER_FUNDING
                )
            if not address_entry:
                address_entry = self._find_address_entry(
                    address, AddressEntryContext.TRADE_PAYOUT
                )
            if not address_entry:
                address_entry = self._find_address_entry(
                    address, AddressEntryContext.ARBITRATOR
                )
            if address_entry:
                address_entries.add(address_entry)

        if not address_entries:
            raise AddressEntryException("No Addresses for withdraw found in our wallet")

        send_request.coin_selector = BtcCoinSelector(
            self._wallets_setup.get_addresses_from_address_entries(address_entries),
            self._preferences.get_ignore_dust_threshold(),
        )

        change_address_entry = None
        if change_address:
            change_address_entry = self._find_address_entry(
                change_address, AddressEntryContext.AVAILABLE
            )

        if not change_address_entry:
            change_address_entry = self.get_fresh_address_entry()

        check_argument(
            change_address_entry is not None, "change address must not be None"
        )
        send_request.change_address = change_address_entry.get_address()

        return send_request

    # We ignore utxos which are considered dust attacks for spying on users' wallets.
    # The ignoreDustThreshold value is set in the preferences. If not set we use default non dust
    # value of 546 sat.
    def is_dust_attack_utxo(self, output: "TransactionOutput"):
        return output.value < self._preferences.get_ignore_dust_threshold()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Find inputs and change
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_inputs_and_change(
        self,
        required: Coin,
    ) -> tuple[list["RawTransactionInput"], Coin]:
        check_state(self.wallet, "Wallet is not initialized yet")
        coin_selector = BtcCoinSelector(
            self._wallets_setup.get_addresses_by_context(AddressEntryContext.AVAILABLE),
            self._preferences.get_ignore_dust_threshold(),
        )
        coin_selection = coin_selector.select(
            required, self.wallet.calculate_all_spend_candidates()
        )

        try:
            change = coin_selector.get_change(required, coin_selection)
        except InsufficientMoneyException as e:
            logger.error(f"Missing funds in get_inputs_and_change. missing={e.missing}")
            raise InsufficientMoneyException(e.missing)

        dummy_tx = Transaction(self.params)
        for tx_input in coin_selection.gathered:
            dummy_tx.add_input(tx_input)
        inputs = [
            RawTransactionInput.from_transaction_input(tx_input)
            for tx_input in dummy_tx.inputs
        ]
        return inputs, change
