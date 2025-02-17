from typing import TYPE_CHECKING
from bisq.common.crypto.encryption import Encryption
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.blindvote.vote_with_proposal_tx_id_list import (
    VoteWithProposalTxIdList,
)
from bisq.core.dao.governance.voteresult.vote_result_exception import (
    VoteResultException,
)
from bisq.core.dao.governance.voteresult.vote_result_service import HashWithStake
from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
from bisq.core.dao.state.model.blockchain.tx_output_type import TxOutputType
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bisq.core.dao.state.model.governance.dao_phase import DaoPhase
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.dao.governance.period.period_service import PeriodService
    from bisq.core.dao.state.dao_state_service import DaoStateService


logger = get_logger(__name__)


class VoteResultConsensus:

    @staticmethod
    def has_op_return_data_valid_length(op_return_data: bytes) -> bool:
        return len(op_return_data) == 38

    @staticmethod
    def get_hash_of_blind_vote_list(op_return_data: bytes) -> bytes:
        return op_return_data[2:22]

    @staticmethod
    def decrypt_votes(
        encrypted_votes: bytes, secret_key: bytes
    ) -> VoteWithProposalTxIdList:
        try:
            decrypted = Encryption.decrypt(encrypted_votes, secret_key)
            return (
                VoteWithProposalTxIdList.get_vote_with_proposal_tx_id_list_from_bytes(
                    decrypted
                )
            )
        except Exception as e:
            raise VoteResultException.DecryptionException(e)

    # We compare first by stake and in case we have multiple entries with same stake we use the
    # hex encoded hashOfProposalList for comparison
    @staticmethod
    def get_majority_hash(hash_with_stake_list: list["HashWithStake"]) -> bytes:
        try:
            check_argument(
                len(hash_with_stake_list) > 0, "hash_with_stake_list must not be empty"
            )
        except Exception as e:
            VoteResultException.ValidationException(e)

        # Sort by stake (descending) and then by hex encoded hash
        # TODO: check if sort is correct
        hash_with_stake_list.sort(key=lambda x: (-x.stake, x.hash.hex()))

        # If there are conflicting data views (multiple hashes) we only consider the voting round as valid if
        # the majority is a super majority with > 80%.
        if len(hash_with_stake_list) > 1:
            total_stake = sum(x.stake for x in hash_with_stake_list)
            stake_of_first = hash_with_stake_list[0].stake
            if stake_of_first / total_stake < 0.8:
                logger.warning(
                    "The winning data view has less than 80% of the total stake of all data views. "
                    "We consider the voting cycle as invalid if the winning data view does not reach "
                    f"a super majority. hash_with_stake_list={hash_with_stake_list}"
                )
                raise VoteResultException.ConsensusException(
                    "The winning data view has less then 80% of the "
                    "total stake of all data views. We consider the voting cycle as invalid if the "
                    "winning data view does not reach a super majority."
                )

        return hash_with_stake_list[0].hash

    @staticmethod
    def get_secret_key(op_return_data: bytes) -> bytes:
        #  Key is stored after version and type bytes and list of Blind votes. It has 16 bytes
        return op_return_data[22:38]

    @staticmethod
    def get_connected_blind_vote_stake_output(
        vote_reveal_tx: "Tx", dao_state_service: "DaoStateService"
    ) -> TxOutput:
        try:
            # We use the stake output of the blind vote tx as first input
            stake_tx_input = vote_reveal_tx.tx_inputs[0]
            blind_vote_stake_output = dao_state_service.get_connected_tx_output(
                stake_tx_input
            )
            check_argument(
                blind_vote_stake_output is not None,
                "blind_vote_stake_output must be present",
            )

            if (
                blind_vote_stake_output.tx_output_type
                != TxOutputType.BLIND_VOTE_LOCK_STAKE_OUTPUT
            ):
                message = f"blind_vote_stake_output must be of type BLIND_VOTE_LOCK_STAKE_OUTPUT but is {blind_vote_stake_output.tx_output_type.name}"
                logger.warning(f"{message}. VoteRevealTx={vote_reveal_tx}")
                raise VoteResultException.ValidationException(
                    f"{message}. VoteRevealTxId={vote_reveal_tx.id}"
                )

            return blind_vote_stake_output
        except VoteResultException.ValidationException as e:
            raise e
        except Exception as e:
            raise VoteResultException.ValidationException(e)

    @staticmethod
    def validate_blind_vote_tx(
        blind_vote_tx_id: str,
        dao_state_service: "DaoStateService",
        period_service: "PeriodService",
        chain_height: int,
    ) -> None:
        try:
            blind_vote_tx = dao_state_service.get_tx(blind_vote_tx_id)
            check_argument(
                blind_vote_tx is not None,
                f"blindVoteTx with txId {blind_vote_tx_id} not found.",
            )

            tx_type = dao_state_service.get_optional_tx_type(blind_vote_tx.id)
            check_argument(
                tx_type is not None,
                f"tx_type must be present. blindVoteTxId={blind_vote_tx.id}",
            )

            check_argument(
                tx_type == TxType.BLIND_VOTE,
                f"blindVoteTx must have type BLIND_VOTE but is {tx_type.name}. blindVoteTxId={blind_vote_tx.id}",
            )

            check_argument(
                period_service.is_tx_in_correct_cycle(
                    blind_vote_tx.block_height, chain_height
                ),
                f"blindVoteTx is not in correct cycle. blindVoteTx.block_height={blind_vote_tx.block_height}. "
                f"chain_height={chain_height}. blindVoteTxId={blind_vote_tx.id}",
            )

            check_argument(
                period_service.is_in_phase(
                    blind_vote_tx.block_height, DaoPhase.Phase.BLIND_VOTE
                ),
                f"blindVoteTx is not in BLIND_VOTE phase. blindVoteTx.block_height={blind_vote_tx.block_height}. "
                f"blindVoteTxId={blind_vote_tx.id}",
            )
        except Exception as e:
            raise VoteResultException.ValidationException(e)
