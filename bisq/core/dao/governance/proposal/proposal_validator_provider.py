from typing import TYPE_CHECKING

from bisq.core.dao.governance.proposal.proposal_type import ProposalType


if TYPE_CHECKING:
    from bisq.core.dao.state.model.governance.proposal import Proposal
    from bisq.core.dao.governance.proposal.compensation.compensation_validator import (
        CompensationValidator,
    )
    from bisq.core.dao.governance.proposal.confiscatebond.confiscate_bond_validator import (
        ConfiscateBondValidator,
    )
    from bisq.core.dao.governance.proposal.generic.generic_proposal_validator import (
        GenericProposalValidator,
    )
    from bisq.core.dao.governance.proposal.param.change_param_validator import (
        ChangeParamValidator,
    )
    from bisq.core.dao.governance.proposal.reimbursement.reimbursement_validator import (
        ReimbursementValidator,
    )
    from bisq.core.dao.governance.proposal.remove_asset.remove_asset_validator import (
        RemoveAssetValidator,
    )
    from bisq.core.dao.governance.proposal.role.role_validator import RoleValidator


class ProposalValidatorProvider:

    def __init__(
        self,
        compensation_validator: "CompensationValidator",
        confiscate_bond_validator: "ConfiscateBondValidator",
        generic_proposal_validator: "GenericProposalValidator",
        change_param_validator: "ChangeParamValidator",
        reimbursement_validator: "ReimbursementValidator",
        remove_asset_validator: "RemoveAssetValidator",
        role_validator: "RoleValidator",
    ):
        self.compensation_validator = compensation_validator
        self.confiscate_bond_validator = confiscate_bond_validator
        self.generic_proposal_validator = generic_proposal_validator
        self.change_param_validator = change_param_validator
        self.reimbursement_validator = reimbursement_validator
        self.remove_asset_validator = remove_asset_validator
        self.role_validator = role_validator

    def get_validator(self, proposal: "Proposal"):
        return self._get_validator_by_type(proposal.get_type())

    def _get_validator_by_type(self, proposal_type: ProposalType):
        if proposal_type == ProposalType.COMPENSATION_REQUEST:
            return self.compensation_validator
        elif proposal_type == ProposalType.REIMBURSEMENT_REQUEST:
            return self.reimbursement_validator
        elif proposal_type == ProposalType.CHANGE_PARAM:
            return self.change_param_validator
        elif proposal_type == ProposalType.BONDED_ROLE:
            return self.role_validator
        elif proposal_type == ProposalType.CONFISCATE_BOND:
            return self.confiscate_bond_validator
        elif proposal_type == ProposalType.GENERIC:
            return self.generic_proposal_validator
        elif proposal_type == ProposalType.REMOVE_ASSET:
            return self.remove_asset_validator
        else:
            raise RuntimeError(
                f"Proposal type {proposal_type.name} was not covered by ProposalValidatorProvider."
            )
