from collections.abc import Callable
from typing import TYPE_CHECKING
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.unconfirmed.unconfirmed_bsq_change_output_list import (
    UnconfirmedBsqChangeOutputList,
)
from bisq.core.dao.state.unconfirmed.unconfirmed_tx_output import UnconfirmedTxOutput
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType

if TYPE_CHECKING:
    from bitcoinj.core.transaction_output import TransactionOutput
    from bitcoinj.wallet.wallet import Wallet
    from bitcoinj.core.transaction import Transaction
    from bisq.common.persistence.persistence_manager import PersistenceManager


class UnconfirmedBsqChangeOutputListService(PersistedDataHost):
    def __init__(
        self, persistence_manager: "PersistenceManager[UnconfirmedBsqChangeOutputList]"
    ):
        self.unconfirmed_bsq_change_output_list = UnconfirmedBsqChangeOutputList()
        self.persistence_manager = persistence_manager

        self.persistence_manager.initialize(
            self.unconfirmed_bsq_change_output_list,
            PersistenceManagerSource.PRIVATE,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        def on_persisted(persisted: "UnconfirmedBsqChangeOutputList"):
            self.unconfirmed_bsq_change_output_list.set_all(persisted.list)
            complete_handler()

        self.persistence_manager.read_persisted(on_persisted, complete_handler)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # Once a tx gets committed to our BSQ wallet we store the change output for allowing it to be spent in follow-up
    # transactions.
    def on_commit_tx(self, tx: "Transaction", tx_type: TxType, wallet: "Wallet"):
        # We remove all potential connected outputs from our inputs as they would have been spent.
        self.remove_connected_outputs_of_inputs_of_tx(tx)

        change_output_index = 0
        if tx_type in (
            TxType.UNDEFINED_TX_TYPE,
            TxType.UNVERIFIED,
            TxType.INVALID,
            TxType.GENESIS,
            TxType.IRREGULAR,
        ):
            return
        elif tx_type == TxType.TRANSFER_BSQ:
            change_output_index = 1  # output 0 is receiver's address
        elif tx_type in (
            TxType.PAY_TRADE_FEE,
            TxType.PROPOSAL,
            TxType.COMPENSATION_REQUEST,
            TxType.REIMBURSEMENT_REQUEST,
        ):
            change_output_index = 0
        elif tx_type == TxType.BLIND_VOTE:
            change_output_index = 1  # output 0 is stake
        elif tx_type == TxType.VOTE_REVEAL:
            change_output_index = 0
        elif tx_type == TxType.LOCKUP:
            change_output_index = 1  # output 0 is lockup amount
        elif tx_type == TxType.UNLOCK:
            # We don't allow to spend the unlocking funds as there is the lock time which need to pass,
            # otherwise the funds get burned!
            return
        elif tx_type in (TxType.ASSET_LISTING_FEE, TxType.PROOF_OF_BURN):
            change_output_index = 0
        else:
            return

        # It can be that we don't have a BSQ and a BTC change output.
        # If no BSQ change but a BTC change the index points to the BTC output and then
        # we detect that it is not part of our wallet.
        # If there is a BSQ change but no BTC change it has no effect as we ignore BTC outputs anyway.
        # If both change outputs do not exist then we might point to an index outside
        # of the list and we return at our scope check.

        # If no BTC output (unlikely but
        # possible) the index points to the BTC output and then we detect that it is not part of our wallet.
        # 
        outputs = tx.outputs
        if change_output_index > len(outputs) - 1:
            return

        change = outputs[change_output_index]
        if not change.is_for_wallet(wallet):
            return

        tx_output = UnconfirmedTxOutput.from_transaction_output(change)
        if self.unconfirmed_bsq_change_output_list.contains_tx_output(tx_output):
            return

        self.unconfirmed_bsq_change_output_list.append(tx_output)
        self.request_persistence()

    def on_reorganize(self):
        self.reset()

    def on_spv_resync(self):
        self.reset()

    def on_transaction_confidence_changed(self, tx: "Transaction"):
        if (
            tx is not None
            and tx.confidence.confidence_type
            == TransactionConfidenceType.BUILDING
        ):
            self.remove_connected_outputs_of_inputs_of_tx(tx)

            for transaction_output in tx.outputs:
                tx_output = UnconfirmedTxOutput.from_transaction_output(
                    transaction_output
                )
                if self.unconfirmed_bsq_change_output_list.contains_tx_output(
                    tx_output
                ):
                    self.unconfirmed_bsq_change_output_list.remove(tx_output)

    def has_transaction_output(self, output: "TransactionOutput") -> bool:
        return self.unconfirmed_bsq_change_output_list.contains_tx_output(
            UnconfirmedTxOutput.from_transaction_output(output)
        )

    def get_balance(self) -> "Coin":
        return Coin.value_of(
            sum(output.value for output in self.unconfirmed_bsq_change_output_list.list)
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def remove_connected_outputs_of_inputs_of_tx(self, tx: "Transaction"):
        for tx_input in tx.inputs:
            connected_output = tx_input.connected_output
            if connected_output is not None:
                tx_output = UnconfirmedTxOutput.from_transaction_output(
                    connected_output
                )
                if self.unconfirmed_bsq_change_output_list.contains_tx_output(
                    tx_output
                ):
                    self.unconfirmed_bsq_change_output_list.remove(tx_output)
                    self.request_persistence()

    def reset(self):
        self.unconfirmed_bsq_change_output_list.clear()
        self.request_persistence()

    def request_persistence(self):
        self.persistence_manager.request_persistence()
