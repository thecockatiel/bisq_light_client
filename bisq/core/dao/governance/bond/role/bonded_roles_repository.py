from typing import TYPE_CHECKING, Optional
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.bond.bond_repository import BondRepository
from bisq.core.dao.governance.bond.role.bonded_role import BondedRole
from bisq.core.dao.state.model.governance.role_proposal import RoleProposal

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.state.model.governance.role import Role


class BondedRolesRepository(BondRepository["BondedRole", "Role"]):

    def is_my_role(self, role: "Role") -> bool:
        my_wallet_transaction_ids = {
            tx.get_tx_id()
            for tx in self._bsq_wallet_service.get_cloned_wallet_transactions()
        }
        return any(
            role_proposal.tx_id in my_wallet_transaction_ids
            for role_proposal in self._get_accepted_bonded_role_proposal_stream()
            if role_proposal.role == role
        )

    def get_accepted_bonded_role_proposal(self, role: "Role") -> Optional["BondedRole"]:
        return next(
            (
                e
                for e in self._get_accepted_bonded_role_proposal_stream()
                if e.role.uid == role.uid
            ),
            None,
        )

    def get_accepted_bonds(self) -> list["BondedRole"]:
        return [
            bonded_role
            for bonded_role in self.bonds
            if self.get_accepted_bonded_role_proposal(bonded_role.bonded_asset)
            is not None
        ]

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_bond(self, role: "Role") -> "BondedRole":
        return BondedRole(role)

    def get_bonded_asset_stream(self):
        return (proposal.role for proposal in self._get_bonded_role_proposal_stream())

    def update_bond(
        self, bond: "BondedRole", bonded_asset: "Role", lockup_tx_output: "TxOutput"
    ) -> None:
        # Lets see if we have a lock up tx.
        lockup_tx_id = lockup_tx_output.tx_id
        lockup_tx = self._dao_state_service.get_tx(lockup_tx_id)
        if lockup_tx:
            op_return_data = lockup_tx.last_tx_output.op_return_data
            # We used the hash of the bonded bondedAsset object as our hash in OpReturn of the lock up tx to have a
            # unique binding of the tx to the data object.
            hash = BondConsensus.get_hash_from_op_return_data(op_return_data)
            candidate_or_null = self.get_bonded_asset_by_hash_map().get(hash, None)
            if bonded_asset == candidate_or_null:
                self.apply_bond_state(
                    self._dao_state_service, bond, lockup_tx, lockup_tx_output
                )

    def _get_bonded_role_proposal_stream(self):
        return (
            ep.proposal
            for ep in self._dao_state_service.get_evaluated_proposal_list()
            if isinstance(ep.proposal, RoleProposal)
        )

    def _get_accepted_bonded_role_proposal_stream(self):
        return (
            ep.proposal
            for ep in self._dao_state_service.get_evaluated_proposal_list()
            if isinstance(ep.proposal, RoleProposal) and ep.is_accepted
        )
