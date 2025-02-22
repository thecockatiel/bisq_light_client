from bisq.core.dao.monitoring.model.state_hash import StateHash
import pb_pb2 as protobuf


class ProposalStateHash(StateHash):

    def __init__(self, cycle_start_block_height: int, hash: bytes, num_proposals: int):
        super().__init__(cycle_start_block_height, hash)
        self.num_proposals = num_proposals

    def to_proto_message(self):
        return protobuf.ProposalStateHash(
            height=self.height,
            hash=self.hash,
            num_proposals=self.num_proposals,
        )

    @staticmethod
    def from_proto(proto: protobuf.ProposalStateHash):
        return ProposalStateHash(
            cycle_start_block_height=proto.height,
            hash=proto.hash,
            num_proposals=proto.num_proposals,
        )

    def __str__(self):
        return (
            "ProposalStateHash{\n"
            f"     numProposals={self.num_proposals}\n"
            "} " + super().__str__()
        )

    def __eq__(self, other):
        if not isinstance(other, ProposalStateHash):
            return False
        return (
            self.height == other.height
            and self.hash == other.hash
            and self.num_proposals == other.num_proposals
        )

    def __hash__(self):
        return hash((self.height, self.hash, self.num_proposals))
