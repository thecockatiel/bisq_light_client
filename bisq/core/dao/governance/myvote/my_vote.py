from datetime import datetime
from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
from bisq.core.dao.governance.merit.merit_consensus import MeritConsensus
from bisq.core.dao.state.model.governance.ballot_list import BallotList
from utils.time import get_time_ms
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.governance.blindvote.my_blind_vote_list_service import (
        MyBlindVoteListService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService


class MyVote(PersistablePayload):
    """
    Holds all my vote related data. Is not immutable as revealTxId is set later. Only used for local persistence and not
    in consensus critical operations.
    """

    def __init__(
        self,
        height: int,
        ballot_list: "BallotList",
        secret_key_encoded: bytes,
        blind_vote: "BlindVote",
        date: int = None,
        reveal_tx_id: Optional[str] = None,
    ):
        if date is None:
            date = get_time_ms()
        self.height = height
        self.ballot_list = ballot_list
        self.secret_key_encoded = secret_key_encoded
        self.blind_vote = blind_vote
        self.date = date
        self.reveal_tx_id = reveal_tx_id

    def to_proto_message(self) -> protobuf.MyVote:
        builder = protobuf.MyVote(
            height=self.height,
            blind_vote=self.blind_vote.to_proto_message(),
            ballot_list=self.ballot_list.to_proto_message(),
            secret_key_encoded=self.secret_key_encoded,
            date=self.date,
            reveal_tx_id=self.reveal_tx_id,
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.MyVote) -> "MyVote":
        return MyVote(
            height=proto.height,
            ballot_list=BallotList.from_proto(proto.ballot_list),
            secret_key_encoded=proto.secret_key_encoded,
            blind_vote=BlindVote.from_proto(proto.blind_vote),
            date=proto.date,
            reveal_tx_id=proto.reveal_tx_id if proto.HasField("reveal_tx_id") else None,
        )

    @property
    def blind_vote_tx_id(self):
        return self.blind_vote.tx_id

    def get_merit(
        self,
        my_blind_vote_list_service: "MyBlindVoteListService",
        dao_state_service: "DaoStateService",
    ):
        merit_list = my_blind_vote_list_service.get_merits(self.blind_vote.tx_id)
        if dao_state_service.get_tx(self.blind_vote.tx_id):
            return MeritConsensus.get_merit_stake(
                self.blind_vote.tx_id, merit_list, dao_state_service
            )
        else:
            return MeritConsensus.get_currently_available_merit(
                merit_list, dao_state_service.chain_height
            )

    def __str__(self):
        return (
            f"MyVote{{\n"
            f"     ballotList={self.ballot_list},\n"
            f"     secretKeyEncoded={bytes_as_hex_string(self.secret_key_encoded)},\n"
            f"     blindVotePayload={self.blind_vote},\n"
            f"     date={datetime.fromtimestamp(self.date/1000)},\n"
            f"     revealTxId='{self.reveal_tx_id}'\n"
            f"}}"
        )
