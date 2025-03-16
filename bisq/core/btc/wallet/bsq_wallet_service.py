from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Iterable, Optional
from bisq.common.user_thread import UserThread
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.btc.wallet.wallet_transactions_change_listener import (
    WalletTransactionsChangeListener,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bitcoinj.base.coin import Coin
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.script.script_type import ScriptType
from electrum_min.elogging import get_logger
from utils.concurrency import ThreadSafeSet

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
    from bitcoinj.core.address import Address
    from bitcoinj.core.transaction_output import TransactionOutput
    from bisq.core.btc.setup.wallets_setup import WalletsSetup
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.listeners.bsq_balance_listener import BsqBalanceListener


logger = get_logger(__name__)


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
        self.wallet = self._wallets_setup.btc_wallet
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
        logger.warning("onReorganize ")
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
        pass

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
        raise RuntimeError(
            "BsqWalletService.sign_tx_and_verify_no_dust_outputs Not implemented yet"
        )

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
        raise RuntimeError(
            "BsqWalletService.get_prepared_send_bsq_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Send BTC (non-BSQ) with BTC fee (e.g. the issuance output from a  lost comp. request)
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Burn fee txs
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_trade_fee_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_trade_fee_tx Not implemented yet"
        )

    def get_prepared_proposal_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_proposal_tx Not implemented yet"
        )

    def get_prepared_issuance_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_issuance_tx Not implemented yet"
        )

    def get_prepared_proof_of_burn_tx(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_proof_of_burn_tx Not implemented yet"
        )

    def get_prepared_burn_fee_tx_for_asset_listing(self, fee: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_burn_fee_tx_for_asset_listing Not implemented yet"
        )

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

    def get_prepared_blind_vote_tx(self, fee: Coin, stake: Coin) -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_blind_vote_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // MyVote reveal tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_vote_reveal_tx(self, stake_tx_output: "TxOutput") -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_vote_reveal_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lockup bond tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_lockup_tx(self, lockup_amount: "Coin") -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_lockup_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Unlock bond tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_prepared_unlock_tx(self, lockup_tx_output: "TxOutput") -> "Transaction":
        raise RuntimeError(
            "BsqWalletService.get_prepared_unlock_tx Not implemented yet"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Addresses
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_unused_address(self) -> "Address":
        unused_address = next(
            (
                address
                for address in self.wallet.get_issued_receive_addresses()
                if ScriptType.P2WPKH == address.output_script_type
                and self.is_address_unused(address)
            ),
            self.wallet.get_receiving_address(),
        )
        return unused_address

    def get_unused_bsq_address_as_string(self) -> str:
        return "B" + str(self.get_unused_address())

    # For BSQ we do not check for dust attack utxos as they are 5.46 BSQ and a considerable value.
    # The default 546 sat dust limit is handled in the BitcoinJ side anyway.
    def is_dust_attack_utxo(self, output):
        return False
