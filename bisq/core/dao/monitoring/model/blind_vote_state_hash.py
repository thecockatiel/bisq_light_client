from bisq.core.dao.monitoring.model.state_hash import StateHash
import pb_pb2 as protobuf


class BlindVoteStateHash(StateHash):

    def __init__(
        self, cycle_start_block_height: int, hash: bytes, num_blind_votes: int
    ):
        super().__init__(cycle_start_block_height, hash)
        self.num_blind_votes = num_blind_votes

    def to_proto_message(self):
        return protobuf.BlindVoteStateHash(
            height=self.height,
            hash=self.hash,
            num_blind_votes=self.num_blind_votes,
        )

    @staticmethod
    def from_proto(proto: protobuf.BlindVoteStateHash):
        return BlindVoteStateHash(
            cycle_start_block_height=proto.height,
            hash=proto.hash,
            num_blind_votes=proto.num_blind_votes,
        )

    def __str__(self):
        return (
            "BlindVoteStateHash{\n"
            f"     num_blind_votes={self.num_blind_votes}\n"
            "} " + super().__str__()
        )

    def __eq__(self, other):
        if not isinstance(other, BlindVoteStateHash):
            return False
        return (
            self.height == other.height
            and self.hash == other.hash
            and self.num_blind_votes == other.num_blind_votes
        )

    def __hash__(self):
        return hash((self.height, self.hash, self.num_blind_votes))
