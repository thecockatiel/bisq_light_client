from typing import TYPE_CHECKING
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.merit.merit_consensus import MeritConsensus
from bisq.core.dao.state.model.governance.ballot_list import BallotList
from bisq.core.dao.state.model.governance.merit_list import MeritList
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService


class DecryptedBallotsWithMerits(PersistablePayload, ImmutableDaoStateModel):
    """Holds all data from a decrypted vote item."""

    def __init__(
        self,
        hash_of_blind_vote_list: bytes,
        blind_vote_tx_id: str,
        vote_reveal_tx_id: str,
        stake: int,
        ballot_list: BallotList,
        merit_list: MeritList,
    ):
        self.hash_of_blind_vote_list = hash_of_blind_vote_list
        self.blind_vote_tx_id = blind_vote_tx_id
        self.vote_reveal_tx_id = vote_reveal_tx_id
        self.stake = stake

        # BallotList and meritList can be empty list in case we don't have a blind vote payload
        self.ballot_list = ballot_list
        self.merit_list = merit_list

    def to_proto_message(self):
        return protobuf.DecryptedBallotsWithMerits(
            hash_of_blind_vote_list=self.hash_of_blind_vote_list,
            blind_vote_tx_id=self.blind_vote_tx_id,
            vote_reveal_tx_id=self.vote_reveal_tx_id,
            stake=self.stake,
            ballot_list=self.ballot_list.get_builder(),
            merit_list=self.merit_list.to_proto_message(),
        )

    @staticmethod
    def from_proto(
        proto: protobuf.DecryptedBallotsWithMerits,
    ) -> "DecryptedBallotsWithMerits":
        return DecryptedBallotsWithMerits(
            hash_of_blind_vote_list=proto.hash_of_blind_vote_list,
            blind_vote_tx_id=proto.blind_vote_tx_id,
            vote_reveal_tx_id=proto.vote_reveal_tx_id,
            stake=proto.stake,
            ballot_list=BallotList.from_proto(proto.ballot_list),
            merit_list=MeritList.from_proto(proto.merit_list),
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_vote(self, proposal_tx_id: str):
        return next(
            (
                ballot.vote
                for ballot in self.ballot_list
                if ballot.tx_id == proposal_tx_id
            ),
            None,
        )

    def get_merit(self, dao_state_service: "DaoStateService"):
        return MeritConsensus.get_merit_stake(
            self.blind_vote_tx_id, self.merit_list, dao_state_service
        )

    def __str__(self):
        return (
            f"DecryptedBallotsWithMerits{{\n"
            f"     hash_of_blind_vote_list={bytes_as_hex_string(self.hash_of_blind_vote_list)},\n"
            f"     blind_vote_tx_id='{self.blind_vote_tx_id}',\n"
            f"     vote_reveal_tx_id='{self.vote_reveal_tx_id}',\n"
            f"     stake={self.stake},\n"
            f"     ballot_list={self.ballot_list},\n"
            f"     merit_list={self.merit_list}\n"
            f"}}"
        )

    def __eq__(self, value):
        if not isinstance(value, DecryptedBallotsWithMerits):
            return False
        return (
            self.hash_of_blind_vote_list == value.hash_of_blind_vote_list
            and self.blind_vote_tx_id == value.blind_vote_tx_id
            and self.vote_reveal_tx_id == value.vote_reveal_tx_id
            and self.stake == value.stake
            and self.ballot_list == value.ballot_list
            and self.merit_list == value.merit_list
        )

    def __hash__(self):
        # This is wrong but we do it anyway
        return hash(
            (
                self.hash_of_blind_vote_list,
                self.blind_vote_tx_id,
                self.vote_reveal_tx_id,
                self.stake,
                self.ballot_list,
                self.merit_list,
            )
        )
