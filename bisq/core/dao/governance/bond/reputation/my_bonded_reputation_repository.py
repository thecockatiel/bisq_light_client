from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.core.btc.wallet.wallet_transactions_change_listener import (
    WalletTransactionsChangeListener,
)
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.bond.bond_repository import BondRepository
from bisq.core.dao.governance.bond.bond_state import BondState
from bisq.core.dao.governance.bond.reputation.my_bonded_reputation import (
    MyBondedReputation,
)
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from utils.data import ObservableList

if TYPE_CHECKING:
    from bisq.core.dao.governance.bond.reputation.my_reputation import MyReputation
    from bisq.core.dao.governance.bond.reputation.my_reputation_list_service import (
        MyReputationListService,
    )
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.state.dao_state_service import DaoStateService


class MyBondedReputationRepository(DaoSetupService, WalletTransactionsChangeListener):
    """
    Collect MyBondedReputations from the myReputationListService and provides access to the collection.
    Gets updated after a new block is parsed or at bsqWallet transaction change to detect also state changes by
    unconfirmed txs.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        bsq_wallet_service: "BsqWalletService",
        my_reputation_list_service: "MyReputationListService",
    ):
        self.logger = get_ctx_logger(__name__)
        self._dao_state_service = dao_state_service
        self._bsq_wallet_service = bsq_wallet_service
        self._my_reputation_list_service = my_reputation_list_service
        self.my_bonded_reputations = ObservableList["MyBondedReputation"]()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        class Listener(DaoStateListener):
            def on_parse_block_complete_after_batch_processing(self_, block):
                self.update()

        self._dao_state_service.add_dao_state_listener(Listener())
        self._bsq_wallet_service.add_wallet_transactions_change_listener(self)

    def start(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // WalletTransactionsChangeListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_wallet_transactions_change(self):
        self.update()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def update(self):
        self.logger.debug("update")
        # It can be that the same salt/hash is in several lockupTxs, so we use the bondByLockupTxIdMap to eliminate
        # duplicates by the collection algorithm.
        bond_by_lockup_tx_id_map = dict[str, "MyBondedReputation"]()
        for my_reputation in self._my_reputation_list_service.my_reputation_list:
            for my_bonded_reputation in self._get_my_bonded_reputation(my_reputation):
                bond_by_lockup_tx_id_map.setdefault(
                    my_bonded_reputation.lockup_tx_id, my_bonded_reputation
                )

        self.my_bonded_reputations.set_all(
            [
                self._update_bond_state(my_bonded_reputation)
                for my_bonded_reputation in bond_by_lockup_tx_id_map.values()
            ]
        )

    def _get_my_bonded_reputation(self, my_reputation: "MyReputation"):
        for lockup_tx_output in self._dao_state_service.get_lockup_tx_outputs():
            lockup_tx_id = lockup_tx_output.tx_id
            lockup_tx = self._dao_state_service.get_tx(lockup_tx_id)
            if lockup_tx:
                op_return_data = lockup_tx.last_tx_output.op_return_data
                hash_ = BondConsensus.get_hash_from_op_return_data(op_return_data)
                # There could be multiple txs with the same hash, so we collect a stream and not use an optional.
                if hash_ == my_reputation.hash:
                    my_bonded_reputation = MyBondedReputation(my_reputation)
                    BondRepository.apply_bond_state(
                        self._dao_state_service,
                        my_bonded_reputation,
                        lockup_tx,
                        lockup_tx_output,
                    )
                    yield my_bonded_reputation

    def _update_bond_state(self, my_bonded_reputation: "MyBondedReputation"):
        if BondRepository.is_confiscated(my_bonded_reputation, self._dao_state_service):
            my_bonded_reputation.bond_state = BondState.CONFISCATED
        else:
            # We don't have a UI use case for showing LOCKUP_TX_PENDING yet, but let's keep the code so if needed
            # it's there.
            if (
                BondRepository.is_lockup_tx_unconfirmed(
                    self._bsq_wallet_service, my_bonded_reputation.bonded_asset
                )
                and my_bonded_reputation.bond_state == BondState.READY_FOR_LOCKUP
            ):
                my_bonded_reputation.bond_state = BondState.LOCKUP_TX_PENDING
            elif (
                BondRepository.is_unlock_tx_unconfirmed(
                    self._bsq_wallet_service,
                    self._dao_state_service,
                    my_bonded_reputation.bonded_asset,
                )
                and my_bonded_reputation.bond_state == BondState.LOCKUP_TX_CONFIRMED
            ):
                my_bonded_reputation.bond_state = BondState.UNLOCK_TX_PENDING
        return my_bonded_reputation
