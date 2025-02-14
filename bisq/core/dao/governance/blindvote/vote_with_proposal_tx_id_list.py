from bisq.common.proto import Proto
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.governance.blindvote.vote_with_proposal_tx_id import (
    VoteWithProposalTxId,
)
import pb_pb2 as protobuf


class VoteWithProposalTxIdList(Proto, ConsensusCritical):
    """
    We encode the VoteWithProposalTxId list to PB bytes in the blindVote. The bytes get encrypted and later decrypted.
    To use a ByteOutputStream and add all list elements would work for encryption but for decrypting we don't know the
    length of a list entry and it would make the process complicated (e.g. require a custom serialisation format).
    """

    def __init__(self, list_: list["VoteWithProposalTxId"]):
        self.list = list_

    @staticmethod
    def from_bytes(bytes_: bytes) -> "VoteWithProposalTxIdList":
        proto = protobuf.VoteWithProposalTxIdList.FromString(bytes_)
        return VoteWithProposalTxIdList.from_proto(proto)

    def to_proto_message(self):
        return protobuf.VoteWithProposalTxIdList(
            item=[item.to_proto_message() for item in self.list]
        )

    @staticmethod
    def from_proto(
        proto: protobuf.VoteWithProposalTxIdList,
    ) -> "VoteWithProposalTxIdList":
        list_ = [VoteWithProposalTxId.from_proto(item) for item in proto.item]
        return VoteWithProposalTxIdList(list_)

    def __str__(self):
        return (
            f"VoteWithProposalTxIdList: {[item.proposal_tx_id for item in self.list]}"
        )
