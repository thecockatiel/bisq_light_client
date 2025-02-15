from bisq.common.protocol.persistable.persistable_list import PersistableList
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
from bisq.core.dao.state.model.governance.proposal import Proposal
import pb_pb2 as protobuf


class MyProposalList(PersistableList[Proposal], ConsensusCritical):
    """PersistableEnvelope wrapper for list of proposals. Used in vote consensus, so changes can break consensus!"""

    def to_proto_message(self):
        return protobuf.PersistableEnvelope(
            my_proposal_list=protobuf.MyProposalList(
                proposal=[proposal.to_proto_message() for proposal in self.list]
            )
        )

    @staticmethod
    def from_proto(proto: protobuf.MyProposalList) -> "MyProposalList":
        proposals = [Proposal.from_proto(p) for p in proto.proposal]
        return MyProposalList(proposals)

    def __str__(self):
        return "List of TxId's in MyProposalList: " + str(
            [proposal.tx_id for proposal in self.list]
        )
