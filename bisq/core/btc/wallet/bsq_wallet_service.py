from collections.abc import Callable
from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Iterable, Optional
from bisq.common.user_thread import UserThread
from bisq.core.btc.exceptions.bsq_change_below_dust_exception import (
    BsqChangeBelowDustException,
)
from bisq.core.btc.exceptions.insufficient_bsq_exception import InsufficientBsqException
from bisq.core.btc.wallet.bisq_default_coin_selector import BisqDefaultCoinSelector
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.btc.wallet.wallet_transactions_change_listener import (
    WalletTransactionsChangeListener,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.blockchain.tx_output_key import TxOutputKey
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.core.transaction_input import TransactionInput
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.script.script_type import ScriptType
from bitcoinj.wallet.send_request import SendRequest
from electrum_min.elogging import get_logger
from utils.concurrency import ThreadSafeSet
from utils.preconditions import check_argument, check_not_none
from utils.time import get_time_ms
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.core.address import Address
from bitcoinj.core.transaction import Transaction

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.btc.wallet.bsq_coin_selector import BsqCoinSelector
    from bisq.core.btc.wallet.non_bsq_coin_selector import NonBsqCoinSelector
    from bisq.core.dao.dao_kill_switch import DaoKillSwitch
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list_service import (
        UnconfirmedBsqChangeOutputListService,
    )
    from bisq.core.util.coin.bsq_formatter import BsqFormatter
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.btc.raw_transaction_input import RawTransactionInput
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.btc.listeners.bsq_balance_listener import BsqBalanceListener


# TODO
class BsqWalletService(WalletService, DaoStateListener):

    def __init__(
        self,
        wallets_setup: "WalletsSetup",
        bsq_coin_selector: "BsqCoinSelector",
        non_bsq_coin_selector: "NonBsqCoinSelector",
        dao_state_service: "DaoStateService",
        unconfirmed_bsq_change_output_list_service: "UnconfirmedBsqChangeOutputListService",
        preferences: "Preferences",
        fee_service: "FeeService",
        dao_kill_switch: "DaoKillSwitch",
        bsq_formatter: "BsqFormatter",
    ):
        super().__init__(wallets_setup, preferences, fee_service)
        self.logger = get_ctx_logger(__name__)
        self._dao_kill_switch = dao_kill_switch
        self._bsq_coin_selector = bsq_coin_selector
        self._non_bsq_coin_selector = non_bsq_coin_selector
        self._dao_state_service = dao_state_service
        self._unconfirmed_bsq_change_output_list_service = (
            unconfirmed_bsq_change_output_list_service
        )
        self._wallet_transactions: list["Transaction"] = []
        self._wallet_transactions_by_id: Optional[dict[str, "Transaction"]] = None
        self._bsq_balance_listeners = ThreadSafeSet["BsqBalanceListener"]()
        self._wallet_transactions_change_listeners = ThreadSafeSet[
            "WalletTransactionsChangeListener"
        ]()
        self._update_bsq_wallet_transactions_pending = False
        self._bsq_formatter = bsq_formatter

        self.available_non_bsq_balance = Coin.ZERO()
        self.available_balance = Coin.ZERO()
        self.unverified_balance = Coin.ZERO()
        self.verified_balance = Coin.ZERO()
        self.unconfirmed_change_balance = Coin.ZERO()
        self.locked_for_voting_balance = Coin.ZERO()
        self.lockup_bonds_balance = Coin.ZERO()
        self.unlocking_bonds_balance = Coin.ZERO()

        wallets_setup.add_setup_completed_handler(self._on_setup_completed)

        dao_state_service.add_dao_state_listener(self)

    @property
    def bsq_formatter(self):
        return self._bsq_formatter

    def _on_setup_completed(self):
        self.wallet = self._wallets_setup.bsq_wallet
        if self.wallet:
            self.add_listeners_to_wallet()

    def add_listeners_to_wallet(self):
        super().add_listeners_to_wallet()
        self.wallet.add_tx_verified_listener(self._on_tx_verified)
        self.wallet.add_new_tx_listener(self._on_new_tx_added)
        self.wallet.add_tx_removed_listener(self._on_tx_removed)

    def _on_tx_verified(self, tx: "Transaction"):
        self._update_bsq_wallet_transactions()
        self._unconfirmed_bsq_change_output_list_service.on_transaction_confidence_changed(
            tx
        )

    def _on_new_tx_added(self, tx: "Transaction"):
        self._update_bsq_wallet_transactions()

    def _on_tx_removed(self, tx: "Transaction"):
        # possible reorg
        self.logger.warning("onReorganize ")
        self._update_bsq_wallet_transactions()
        self._unconfirmed_bsq_change_output_list_service.on_reorganize()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        if self.is_wallet_ready:
            for tx in self.wallet.get_transactions():
                self._unconfirmed_bsq_change_output_list_service.on_transaction_confidence_changed(
                    tx
                )
            self._update_bsq_wallet_transactions()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Overridden Methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Balance
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _update_bsq_balance(self):
        ts = get_time_ms()
        self.unverified_balance = Coin.value_of(
            sum(
                # Sum up outputs into BSQ wallet and subtract the inputs using lockup or unlocking
                # outputs since those inputs will be accounted for in lockupBondsBalance and
                # unlockingBondsBalance
                sum(
                    out_.value
                    for out_ in tx.outputs
                    if out_.is_for_wallet(self.wallet) and out_.available_for_spending
                )
                -
                # Account for spending of locked connectedOutputs
                sum(
                    in_.value
                    for in_ in tx.inputs
                    if in_.connected_output
                    and (key := TxOutputKey(tx.get_tx_id(), in_.connected_output.index))
                    and in_.connected_output.is_for_wallet(self.wallet)
                    and (
                        self._dao_state_service.is_lockup_output(key)
                        or self._dao_state_service.is_unlocking_and_unspent_key(key)
                    )
                )
                for tx in self.wallet.get_transactions()
                if tx.confidence.confidence_type == TransactionConfidenceType.PENDING
            )
        )

        confirmed_tx_id_set = {
            tx.get_tx_id()
            for tx in self.wallet.get_transactions()
            if tx.confidence.confidence_type == TransactionConfidenceType.BUILDING
        }

        self.locked_for_voting_balance = Coin.value_of(
            sum(
                tx_output.value
                for tx_output in self._dao_state_service.get_unspent_blind_vote_stake_tx_outputs()
                if tx_output.tx_id in confirmed_tx_id_set
            )
        )

        self.lockup_bonds_balance = Coin.value_of(
            sum(
                tx_output.value
                for tx_output in self._dao_state_service.get_lockup_tx_outputs()
                if self._dao_state_service.is_unspent(tx_output.get_key())
                and not self._dao_state_service.is_confiscated_lockup_tx_output(
                    tx_output.tx_id
                )
                and tx_output.tx_id in confirmed_tx_id_set
            )
        )

        self.unlocking_bonds_balance = Coin.value_of(
            sum(
                tx_output.value
                for tx_output in self._dao_state_service.get_unspent_unlocking_tx_outputs_stream()
                if tx_output.tx_id in confirmed_tx_id_set
                and not self._dao_state_service.is_confiscated_unlock_tx_output(
                    tx_output.tx_id
                )
            )
        )

        self.available_balance = self._bsq_coin_selector.select(
            NetworkParameters.MAX_MONEY, self.wallet.calculate_all_spend_candidates()
        ).value_gathered

        if self.available_balance.is_negative():
            self.available_balance = Coin.ZERO()

        self.unconfirmed_change_balance = (
            self._unconfirmed_bsq_change_output_list_service.get_balance()
        )

        self.available_non_bsq_balance = self._non_bsq_coin_selector.select(
            NetworkParameters.MAX_MONEY, self.wallet.calculate_all_spend_candidates()
        ).value_gathered

        self.verified_balance = self.available_balance.subtract(
            self.unconfirmed_change_balance
        )

        for listener in self._bsq_balance_listeners:
            listener(
                self.available_balance,
                self.available_non_bsq_balance,
                self.unverified_balance,
                self.unconfirmed_change_balance,
                self.locked_for_voting_balance,
                self.lockup_bonds_balance,
                self.unlocking_bonds_balance,
            )

        self.logger.info(f"updateBsqBalance took {get_time_ms() - ts} ms")

    def add_bsq_balance_listener(self, listener: "BsqBalanceListener"):
        self._bsq_balance_listeners.add(listener)

    def remove_bsq_balance_listener(self, listener: "BsqBalanceListener"):
        self._bsq_balance_listeners.discard(listener)

    def add_wallet_transactions_change_listener(self, listener: Callable[[], None]):
        self._wallet_transactions_change_listeners.add(listener)

    def remove_wallet_transactions_change_listener(self, listener: Callable[[], None]):
        self._wallet_transactions_change_listeners.discard(listener)

    def get_spendable_bsq_transaction_outputs(self) -> list["TransactionOutput"]:
        return self._bsq_coin_selector.select(
            NetworkParameters.MAX_MONEY, self.wallet.calculate_all_spend_candidates()
        ).gathered.copy()

    def get_spendable_non_bsq_transaction_outputs(self) -> list["TransactionOutput"]:
        return self._non_bsq_coin_selector.select(
            NetworkParameters.MAX_MONEY, self.wallet.calculate_all_spend_candidates()
        ).gathered.copy()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BSQ TransactionOutputs and Transactions
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_cloned_wallet_transactions(self) -> list["Transaction"]:
        return self._wallet_transactions.copy()

    def get_pending_wallet_transactions_stream(self) -> Iterable["Transaction"]:
        return (
            tx
            for tx in self._wallet_transactions
            # tx.confidence is always set here, because get_transactions always sets it
            if tx.confidence.confidence_type == TransactionConfidenceType.PENDING
        )

    def _update_bsq_wallet_transactions(self):
        if self._dao_state_service.parse_block_chain_complete:
            # We get called updateBsqWalletTransactions multiple times from onWalletChanged, onTransactionConfidenceChanged
            # and from onParseBlockCompleteAfterBatchProcessing. But as updateBsqBalance is an expensive operation we do
            # not want to call it in a short interval series so we use a flag and a delay to not call it multiple times
            # in a 100 ms period.
            if not self._update_bsq_wallet_transactions_pending:
                self._update_bsq_wallet_transactions_pending = True

                def update():
                    try:
                        self._wallet_transactions.clear()
                        self._wallet_transactions.extend(self.get_transactions())
                        self._wallet_transactions_by_id = None
                        for listener in self._wallet_transactions_change_listeners:
                            listener.on_wallet_transactions_change()
                        self._update_bsq_balance()
                    finally:
                        self._update_bsq_wallet_transactions_pending = False

                UserThread.run_after(update, timedelta(milliseconds=100))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Sign tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def sign_tx_and_verify_no_dust_outputs(self, tx: "Transaction") -> "Transaction":
        # TODO: check if this works correctly
        if self.wallet.sign_tx(self.password, tx) is None:
            raise IllegalStateException("Failed to sign tx")
        WalletService.verify_non_dust_txo(tx)
        return tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Commit tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def commit_tx(self, tx: "Transaction", tx_type: "TxType") -> None:
        self.wallet.maybe_add_transaction(tx)
        # WalletService.print_tx("BSQ commit Tx", tx)
        self._unconfirmed_bsq_change_output_list_service.on_commit_tx(
            tx, tx_type, self.wallet
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Send BSQ with BTC fee
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_send_bsq_tx(
        self,
        receiver_address: str,
        receiver_amount: Coin,
        utxo_candidates: Optional[set["TransactionOutput"]] = None,
    ) -> "Transaction":
        if utxo_candidates is not None:
            self._bsq_coin_selector.utxo_candidates = utxo_candidates

        return self._get_prepared_send_tx(
            receiver_address, receiver_amount, self._bsq_coin_selector
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Send BTC (non-BSQ) with BTC fee (e.g. the issuance output from a  lost comp. request)
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_send_btc_tx(
        self,
        receiver_address: str,
        receiver_amount: Coin,
        utxo_candidates: Optional[set["TransactionOutput"]] = None,
    ) -> "Transaction":
        if utxo_candidates is not None:
            self._non_bsq_coin_selector.utxo_candidates = utxo_candidates

        return self._get_prepared_send_tx(
            receiver_address, receiver_amount, self._non_bsq_coin_selector
        )

    def _get_prepared_send_tx(
        self,
        receiver_address: str,
        receiver_amount: Coin,
        coin_selector: "BisqDefaultCoinSelector",
    ) -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()
        tx = Transaction(self.params)
        check_argument(
            Restrictions.is_above_dust(receiver_amount),
            "The amount is too low (dust limit).",
        )
        tx.add_output(
            TransactionOutput.from_coin_and_address(
                receiver_amount, Address.from_string(receiver_address, self.params), tx
            )
        )
        try:
            selection = coin_selector.select(
                receiver_amount, self.wallet.calculate_all_spend_candidates()
            )
            change = coin_selector.get_change(receiver_amount, selection)
            if Restrictions.is_above_dust(change):
                tx.add_output(
                    TransactionOutput.from_coin_and_address(
                        change, self._get_change_address(), tx
                    )
                )
            elif not change.is_zero():
                msg = f"BSQ change output is below dust limit. outputValue={change.value / 100} BSQ"
                self.logger.warning(msg)
                raise BsqChangeBelowDustException(msg, change)

            send_request = SendRequest.for_tx(tx)
            send_request.fee = Coin.ZERO()
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False
            send_request.password = self.password
            send_request.shuffle_outputs = False
            send_request.sign_inputs = False
            send_request.change_address = self._get_change_address()
            send_request.coin_selector = coin_selector
            self.wallet.complete_tx(send_request)
            WalletService.check_wallet_consistency(self.wallet)
            WalletService.verify_non_dust_txo(tx)
            coin_selector.utxo_candidates = None  # We reuse the selectors. Reset the transactionOutputCandidates field
            return tx
        except InsufficientMoneyException as e:
            self.logger.error(f"_get_prepared_send_tx: tx={tx}")
            self.logger.error(str(e))
            raise InsufficientBsqException(e.missing)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Burn fee txs
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_trade_fee_tx(self, fee: Coin) -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()

        tx = Transaction(self.params)
        self._add_inputs_and_change_output_for_tx(tx, fee, self._bsq_coin_selector)
        return tx

    # We create a tx with Bsq inputs for the fee and optional BSQ change output.
    # As the fee amount will be missing in the output those BSQ fees are burned.
    def get_prepared_proposal_tx(self, fee: Coin) -> "Transaction":
        return self._get_prepared_tx_with_mandatory_bsq_change_output(fee)

    def get_prepared_issuance_tx(self, fee: Coin) -> "Transaction":
        return self._get_prepared_tx_with_mandatory_bsq_change_output(fee)

    def get_prepared_proof_of_burn_tx(self, fee: Coin) -> "Transaction":
        return self._get_prepared_tx_with_mandatory_bsq_change_output(fee)

    def get_prepared_burn_fee_tx_for_asset_listing(self, fee: Coin) -> "Transaction":
        return self._get_prepared_tx_with_mandatory_bsq_change_output(fee)

    # We need to require one BSQ change output as we could otherwise not be able to distinguish between 2
    # structurally same transactions where only the BSQ fee is different. In case of asset listing fee and proof of
    # burn it is a user input, so it is not known to the parser, instead we derive the burned fee from the parser.

    # In case of proposal fee we could derive it from the params.

    # For issuance txs we also require a BSQ change output before the issuance output gets added. There was a
    # minor bug with the old version that multiple inputs would have caused an exception in case there was no
    # change output (e.g. inputs of 21 and 6 BSQ for BSQ fee of 21 BSQ would have caused that only 1 input was used
    # and then caused an error as we enforced a change output. This new version handles such cases correctly.

    # Examples for the structurally indistinguishable transactions:
    # Case 1: 10 BSQ fee to burn
    # In: 17 BSQ
    # Out: BSQ change 7 BSQ -> valid BSQ
    # Out: OpReturn
    # Miner fee: 1000 sat  (10 BSQ burned)

    # Case 2: 17 BSQ fee to burn
    # In: 17 BSQ
    # Out: burned BSQ change 7 BSQ -> BTC (7 BSQ burned)
    # Out: OpReturn
    # Miner fee: 1000 sat  (10 BSQ burned)

    def _get_prepared_tx_with_mandatory_bsq_change_output(
        self, fee: Coin
    ) -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()

        tx = Transaction(self.params)
        # We look for inputs covering our BSQ fee we want to pay.
        coin_selection = self._bsq_coin_selector.select(
            fee, self.wallet.calculate_all_spend_candidates()
        )
        try:
            change = self._bsq_coin_selector.get_change(fee, coin_selection)
            if change.is_zero() or Restrictions.is_dust(change):
                # If change is zero or below dust, we increase required input amount to enforce a BSQ change output.
                # All outputs after that are considered BTC and therefore would be burned BSQ if BSQ is left from what
                # we use for miner fee.

                min_dust_threshold = Coin.value_of(
                    self._preferences.get_ignore_dust_threshold()
                )
                increased_required_input = fee.add(min_dust_threshold)
                coin_selection = self._bsq_coin_selector.select(
                    increased_required_input,
                    self.wallet.calculate_all_spend_candidates(),
                )
                change = self._bsq_coin_selector.get_change(fee, coin_selection)

                self.logger.warning(
                    f"We increased required input as change output was zero or dust: New change value={change}",
                )
                info = (
                    f"Available BSQ balance={coin_selection.value_gathered.value / 100} BSQ. "
                    f"Intended fee to burn={fee.value / 100} BSQ. "
                    f"Please increase your balance to at least "
                    f"{(fee.value + min_dust_threshold.value) / 100} BSQ."
                )
                check_argument(
                    coin_selection.value_gathered > fee,
                    f"This transaction requires a change output of at least {min_dust_threshold.value / 100} BSQ (dust limit). {info}",
                )

                check_argument(
                    not Restrictions.is_dust(change),
                    f"This transaction would create a dust output of {change.value / 100} BSQ. "
                    f"It requires a change output of at least {min_dust_threshold.value / 100} BSQ (dust limit). {info}",
                )

            for gathered_input in coin_selection.gathered:
                tx.add_input(gathered_input)
            tx.add_output(
                TransactionOutput.from_coin_and_address(
                    change, self._get_change_address(), tx
                )
            )

            return tx

        except InsufficientMoneyException as e:
            self.logger.error(f"coinSelection.gathered={coin_selection.gathered}")
            raise InsufficientBsqException(e.missing)

    def _add_inputs_and_change_output_for_tx(
        self, tx: "Transaction", fee: Coin, bsq_coin_selector: "BsqCoinSelector"
    ) -> None:
        # If our fee is less then dust limit we increase it so we are sure to not get any dust output.
        if Restrictions.is_dust(fee):
            required_input = fee.add(Restrictions.get_min_non_dust_output())
        else:
            required_input = fee

        coin_selection = bsq_coin_selector.select(
            required_input, self.wallet.calculate_all_spend_candidates()
        )
        for gathered_input in coin_selection.gathered:
            tx.add_input(gathered_input)

        try:
            change = bsq_coin_selector.get_change(fee, coin_selection)
            # Change can be ZERO, then no change output is created so don't rely on a BSQ change output
            if change.is_positive():
                check_argument(
                    Restrictions.is_above_dust(change),
                    f"The change output of {change.value / 100:.2f} BSQ is below the min. dust value of "
                    f"{Restrictions.get_min_non_dust_output().value / 100:.2f} BSQ. At least "
                    f"{Restrictions.get_min_non_dust_output().add(fee).value / 100:.2f} BSQ is needed for this transaction",
                )
                tx.add_output(
                    TransactionOutput.from_coin_and_address(
                        change, self._get_change_address(), tx
                    )
                )
        except InsufficientMoneyException as e:
            self.logger.error(str(tx))
            raise InsufficientBsqException(e.missing)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BsqSwap tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_buyers_bsq_inputs_for_bsq_swap_tx(
        self, required: Coin
    ) -> tuple[list["RawTransactionInput"], Coin]:
        raise RuntimeError(
            "BsqWalletService.get_buyers_bsq_inputs_for_bsq_swap_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Blind vote tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We create a tx with Bsq inputs for the fee, one output for the stake and optional one BSQ change output.
    # As the fee amount will be missing in the output those BSQ fees are burned.
    def get_prepared_blind_vote_tx(self, fee: Coin, stake: Coin) -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()
        tx = Transaction(self.params)
        tx.add_output(
            TransactionOutput.from_coin_and_address(
                stake, self.get_unused_address(), tx
            )
        )
        self._add_inputs_and_change_output_for_tx(
            tx, fee.add(stake), self._bsq_coin_selector
        )
        # WalletService.print_tx("getPreparedBlindVoteTx", tx)
        return tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MyVote reveal tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_vote_reveal_tx(self, stake_tx_output: "TxOutput") -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()
        tx = Transaction(self.params)
        stake = Coin.value_of(stake_tx_output.value)
        blind_vote_tx = self.wallet.get_transaction(stake_tx_output.tx_id)
        check_not_none(blind_vote_tx, "blind_vote_tx must not be null")
        # TODO: double check later
        tx.add_input(TransactionInput.from_output(stake_tx_output))
        tx.add_output(
            TransactionOutput.from_coin_and_address(
                stake, self.get_unused_address(), tx
            )
        )
        # WalletService.print_tx("getPreparedVoteRevealTx", tx)
        return tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lockup bond tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_lockup_tx(self, lockup_amount: "Coin") -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()
        tx = Transaction(self.params)
        check_argument(
            Restrictions.is_above_dust(lockup_amount),
            "The amount is too low (dust limit).",
        )
        tx.add_output(
            TransactionOutput.from_coin_and_address(
                lockup_amount, self.get_unused_address(), tx
            )
        )
        self._add_inputs_and_change_output_for_tx(
            tx, lockup_amount, self._bsq_coin_selector
        )
        WalletService.print_tx("prepareLockupTx", tx)
        return tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Unlock bond tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_unlock_tx(self, lockup_tx_output: "TxOutput") -> "Transaction":
        self._dao_kill_switch.assert_dao_is_not_disabled()
        tx = Transaction(self.params)
        # Unlocking means spending the full value of the locked txOutput to another txOutput with the same value
        amount_to_unlock = Coin.value_of(lockup_tx_output.value)
        check_argument(
            Restrictions.is_above_dust(amount_to_unlock),
            "The amount is too low (dust limit).",
        )
        lockup_tx = self.wallet.get_transaction(lockup_tx_output.tx_id)
        check_not_none(lockup_tx, "lockup_tx must not be null")
        # TODO: double check later
        tx.add_input(TransactionInput.from_output(lockup_tx_output))
        tx.add_output(
            TransactionOutput.from_coin_and_address(
                amount_to_unlock, self.get_unused_address(), tx
            )
        )
        WalletService.print_tx("prepareUnlockTx", tx)
        return tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Addresses
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _get_change_address(self) -> "Address":
        return self.get_unused_address(True)

    def get_unused_address(self, for_change=False) -> "Address":
        unused_address = next(
            (
                address
                for address in self.wallet.get_issued_receive_addresses()
                if ScriptType.P2WPKH == address.output_script_type
                and self.is_address_unused(address)
            ),
            None,
        )
        if unused_address is None:
            unused_address = self.wallet.fresh_receive_address(for_change)
        return unused_address

    def get_unused_bsq_address_as_string(self) -> str:
        return "B" + str(self.get_unused_address())

    # For BSQ we do not check for dust attack utxos as they are 5.46 BSQ and a considerable value.
    # The default 546 sat dust limit is handled in the BitcoinJ side anyway.
    def is_dust_attack_utxo(self, output):
        return False
