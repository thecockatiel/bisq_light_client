from typing import Optional
import pb_pb2 as protobuf
from bisq.core.dao.state.model.governance.vote import Vote
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload


class VoteWithProposalTxId(PersistablePayload):

    def __init__(self, proposal_tx_id: str, vote: Optional["Vote"]):
        self.proposal_tx_id = proposal_tx_id
        self.vote = vote

    # Used for sending over the network
    def to_proto_message(self):
        return protobuf.VoteWithProposalTxId(
            proposal_tx_id=self.proposal_tx_id,
            vote=self.vote.to_proto_message() if self.vote else None,
        )

    @staticmethod
    def from_proto(proto: protobuf.VoteWithProposalTxId) -> "VoteWithProposalTxId":
        return VoteWithProposalTxId(
            proposal_tx_id=proto.proposal_tx_id,
            vote=Vote.from_proto(proto.vote) if proto.HasField("vote") else None,
        )
