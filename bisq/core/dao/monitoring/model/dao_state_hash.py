from bisq.core.dao.monitoring.model.state_hash import StateHash
import pb_pb2 as protobuf


class DaoStateHash(StateHash):
    def __init__(self, height: int, hash: bytes, is_self_created: bool):
        super().__init__(height, hash)
        # If we have built the hash by ourselves opposed to that we got delivered the hash from seed nodes or resources
        self.is_self_created = is_self_created

    def to_proto_message(self) -> protobuf.DaoStateHash:
        return protobuf.DaoStateHash(
            height=self.height,
            hash=self.hash,
            is_self_created=self.is_self_created,
        )

    @staticmethod
    def from_proto(proto: protobuf.DaoStateHash) -> "DaoStateHash":
        return DaoStateHash(
            height=proto.height,
            hash=proto.hash,
            is_self_created=proto.is_self_created,
        )

    def __str__(self) -> str:
        return (
            f"DaoStateHash{{\n"
            f"    is_self_created={self.is_self_created}\n"
            f"}} {super().__str__()}"
        )
