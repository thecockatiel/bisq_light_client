from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.bond.bond_repository import BondRepository
from bisq.core.dao.governance.bond.reputation.bonded_reputation import BondedReputation

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.governance.bond.role.bonded_role_repository import (
        BondedRolesRepository,
    )
    from bisq.core.dao.governance.bond.reputation.reputation import Reputation
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput


class BondedReputationRepository(BondRepository["BondedReputation", "Reputation"]):
    """
    Collect bonded reputations from the daoState blockchain data excluding bonded roles
    and provides access to the collection.
    Gets updated after a new block is parsed or at bsqWallet transaction change to detect also state changes by
    unconfirmed txs.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        bsq_wallet_service: "BsqWalletService",
        bonded_roles_repository: "BondedRolesRepository",
    ):
        super().__init__(dao_state_service, bsq_wallet_service)
        self._bonded_roles_repository = bonded_roles_repository

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        super().add_listeners()

        # As event listeners do not have a deterministic ordering of callback we need to ensure
        # that we get updated our data after the bondedRolesRepository was updated.
        # The update gets triggered by daoState or wallet changes. It could be that we get triggered first the
        # listeners and update our data with stale data from bondedRolesRepository. After that the bondedRolesRepository
        # gets triggered the listeners and we would miss the current state if we would not listen here as well on the
        # bond list.
        self._bonded_roles_repository.bonds.add_listener(lambda _: self.update())

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_bond(self, reputation: "Reputation") -> "BondedReputation":
        return BondedReputation(reputation)

    def get_bonded_asset_stream(self):
        return (bond.bonded_asset for bond in self.get_bonded_reputation_stream())

    def update(self):
        self._bond_by_uid_map.clear()
        for bonded_reputation in self.get_bonded_reputation_stream():
            self._bond_by_uid_map[bonded_reputation.bonded_asset.uid] = (
                bonded_reputation
            )
        self.bonds.set_all(self._bond_by_uid_map.values())

    def get_bonded_reputation_stream(self):
        return filter(
            lambda x: x is not None,
            (
                self.__create_bonded_reputation(lockup_tx_output)
                for lockup_tx_output in self.get_lockup_tx_outputs_for_bonded_reputation()
            ),
        )

    def __create_bonded_reputation(
        self, lockup_tx_output: "TxOutput"
    ) -> Optional["BondedReputation"]:
        lockup_tx_id = lockup_tx_output.tx_id
        op_return_tx_output = self._dao_state_service.get_lockup_op_return_tx_output(
            lockup_tx_id
        )
        if op_return_tx_output:
            hash = BondConsensus.get_hash_from_op_return_data(
                op_return_tx_output.op_return_data
            )
            bonded_reputation = BondedReputation(Reputation(hash))
            self.update_bond(bonded_reputation, lockup_tx_output)
            return bonded_reputation
        return None

    def get_lockup_tx_outputs_for_bonded_reputation(self):
        # We exclude bonded roles, so we store those in a lookup set.
        bonded_roles_lockup_tx_id_set = {
            bond.lockup_tx_id
            for bond in self._bonded_roles_repository.bonds
            if bond.lockup_tx_id
        }
        return filter(
            lambda e: e.tx_id not in bonded_roles_lockup_tx_id_set,
            self._dao_state_service.get_lockup_tx_outputs(),
        )

    def update_bond(
        self,
        bond: "BondedReputation",
        lockup_tx_output: "TxOutput",
    ):
        # Lets see if we have a lock up tx.
        lockup_tx_id = lockup_tx_output.tx_id
        tx = self._dao_state_service.get_tx(lockup_tx_id)
        if tx:
            BondRepository.apply_bond_state(
                self._dao_state_service, bond, tx, lockup_tx_output
            )
