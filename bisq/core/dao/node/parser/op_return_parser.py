from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.asset.asset_consensus import AssetConsensus
from bisq.core.dao.governance.blindvote.blind_vote_consensus import BlindVoteConsensus
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.proofofburn.proof_of_burn_consensus import (
    ProofOfBurnConsensus,
)
from bisq.core.dao.governance.proposal.proposal_consensus import ProposalConsensus
from bisq.core.dao.governance.voteresult.vote_result_consensus import (
    VoteResultConsensus,
)
from bisq.core.dao.node.parser.exceptions.invalid_parsing_condition_exception import (
    InvalidParsingConditionException,
)
from bisq.core.dao.node.parser.temp_tx_output import TempTxOutput
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType

logger = get_logger(__name__)


class OpReturnParser:
    """Processes OpReturn output if valid and delegates validation to specific validators."""

    def get_tx_output_type(temp_tx_output: TempTxOutput) -> TxOutputType:
        non_zero_output = temp_tx_output.value != 0
        op_return_data = temp_tx_output.op_return_data
        assert op_return_data is not None, "op_return_data must not be None"

        if non_zero_output or len(op_return_data) < 22:
            logger.warning(
                f"OP_RETURN data does not match our rules. op_return_data={bytes_as_hex_string(op_return_data)}"
            )
            return TxOutputType.INVALID_OUTPUT

        op_return_type = OpReturnType.get_op_return_type(op_return_data[0:1])
        if not op_return_type:
            logger.warning(
                f"OP_RETURN data does not match our defined types. op_return_data={bytes_as_hex_string(op_return_data)}"
            )
            return TxOutputType.INVALID_OUTPUT

        if op_return_type == OpReturnType.PROPOSAL:
            if ProposalConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.PROPOSAL_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.COMPENSATION_REQUEST:
            if ProposalConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.COMP_REQ_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.REIMBURSEMENT_REQUEST:
            if ProposalConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.REIMBURSEMENT_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.BLIND_VOTE:
            if BlindVoteConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.BLIND_VOTE_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.VOTE_REVEAL:
            if VoteResultConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.VOTE_REVEAL_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.LOCKUP:
            if not BondConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.INVALID_OUTPUT
            optional_lockup_reason = BondConsensus.get_lockup_reason(op_return_data)
            if not optional_lockup_reason:
                logger.warning(
                    f"No lockupReason found for lockup tx, op_return_data={bytes_as_hex_string(op_return_data)}",
                )
                return TxOutputType.INVALID_OUTPUT
            lock_time = BondConsensus.get_lock_time(op_return_data)
            if BondConsensus.is_lock_time_in_valid_range(lock_time):
                return TxOutputType.LOCKUP_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.ASSET_LISTING_FEE:
            if AssetConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.ASSET_LISTING_FEE_OP_RETURN_OUTPUT
        elif op_return_type == OpReturnType.PROOF_OF_BURN:
            if ProofOfBurnConsensus.has_op_return_data_valid_length(op_return_data):
                return TxOutputType.PROOF_OF_BURN_OP_RETURN_OUTPUT
        else:
            raise InvalidParsingConditionException(
                "We must have a defined opReturnType as it was checked earlier in the caller."
            )

        logger.info(
            "We expected a compensation request op_return data but it did not match our rules."
        )
        return TxOutputType.INVALID_OUTPUT
