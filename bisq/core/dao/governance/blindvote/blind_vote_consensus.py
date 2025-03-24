from typing import TYPE_CHECKING
from bisq.common.crypto.encryption import Encryption
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.common.version import Version
from bisq.core.dao.governance.blindvote.vote_with_proposal_tx_id_list import (
    VoteWithProposalTxIdList,
)
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from bisq.core.dao.state.model.governance.ballot_list import BallotList
from bitcoinj.base.coin import Coin
from io import BytesIO

from utils.java_compat import java_cmp_str

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.governance.merit_list import MeritList
    from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
    from bisq.core.dao.governance.ballot.ballot_list_service import BallotListService
    from bisq.core.dao.governance.blindvote.blind_vote_list_service import (
        BlindVoteListService,
    )

logger = get_logger(__name__)


class BlindVoteConsensus:
    """All consensus critical aspects are handled here."""

    @staticmethod
    def has_op_return_data_valid_length(op_return_data: bytes) -> bool:
        return len(op_return_data) == 22

    @staticmethod
    def get_sorted_ballot_list(
        ballot_list_service: "BallotListService",
    ) -> "BallotList":
        ballot_list = ballot_list_service.get_valid_ballots_of_cycle()
        sorted_list = sorted(ballot_list, key=lambda ballot: java_cmp_str(ballot.tx_id))
        logger.info(f"Sorted ballotList: {sorted_list}")
        return BallotList(sorted_list)

    @staticmethod
    def get_sorted_blind_vote_list_of_cycle(
        blind_vote_list_service: "BlindVoteListService",
    ) -> list["BlindVote"]:
        blind_vote_list = blind_vote_list_service.get_blind_votes_in_phase_and_cycle()
        return BlindVoteConsensus._get_sorted_blind_vote_list_of_cycle(blind_vote_list)

    @staticmethod
    def _get_sorted_blind_vote_list_of_cycle(
        blind_vote_list: list["BlindVote"],
    ) -> list["BlindVote"]:
        sorted_list = sorted(blind_vote_list, key=lambda vote: java_cmp_str(vote.tx_id))
        logger.debug(
            f"Sorted blindVote txId list: {[vote.tx_id for vote in sorted_list]}"
        )
        return sorted_list

    @staticmethod
    def create_secret_key() -> bytes:
        # 128 bit AES key is good enough for our use case
        return Encryption.generate_secret_key(128)

    @staticmethod
    def get_encrypted_votes(
        vote_with_proposal_tx_id_list: "VoteWithProposalTxIdList", secret_key: bytes
    ) -> bytes:
        bytes_data = vote_with_proposal_tx_id_list.serialize()
        encrypted = Encryption.encrypt(bytes_data, secret_key)
        logger.info(f"EncryptedVotes: {bytes_as_hex_string(encrypted)}")
        return encrypted

    @staticmethod
    def get_encrypted_merit_list(merit_list: "MeritList", secret_key: bytes) -> bytes:
        bytes_data = merit_list.serialize()
        return Encryption.encrypt(bytes_data, secret_key)

    @staticmethod
    def get_hash_of_encrypted_votes(encrypted_votes: bytes) -> bytes:
        return get_sha256_ripemd160_hash(encrypted_votes)

    @staticmethod
    def get_op_return_data(hash: bytes) -> bytes:
        with BytesIO() as output_stream:
            output_stream.write(bytes([OpReturnType.BLIND_VOTE.type]))
            output_stream.write(Version.BLIND_VOTE)
            output_stream.write(hash)
            bytes_data = output_stream.getvalue()
            logger.info(f"OpReturnData: {bytes_as_hex_string(bytes_data)}")
            return bytes_data

    @staticmethod
    def get_fee(dao_state_service: "DaoStateService", chain_height: int) -> "Coin":
        return dao_state_service.get_param_value_as_coin(
            Param.BLIND_VOTE_FEE, chain_height
        )
