from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.utilities import bytes_as_hex_string
import pb_pb2 as protobuf


class MyProofOfBurn(PersistablePayload, NetworkPayload):
    """MyProofOfBurn is persisted locally and holds the preImage and txId."""

    def __init__(self, tx_id: str, pre_image: str):
        self.tx_id = tx_id
        self.pre_image = pre_image
        # Not persisted as it is derived from preImage. Stored for caching purpose only.
        self.hash = get_sha256_ripemd160_hash(pre_image.encode("utf-8"))  # transient

    def to_proto_message(self):
        return protobuf.MyProofOfBurn(
            tx_id=self.tx_id,
            pre_image=self.pre_image,
        )

    @staticmethod
    def from_proto(proto: protobuf.MyProofOfBurn):
        return MyProofOfBurn(
            proto.tx_id,
            proto.pre_image,
        )

    def __str__(self):
        return (
            f"MyProofOfBurn{{\n"
            f"     txId='{self.tx_id}',\n"
            f"     preImage='{self.pre_image}',\n"
            f"     hash='{bytes_as_hex_string(self.hash)}'\n"
            f"}}"
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, MyProofOfBurn):
            return False
        return self.tx_id == other.tx_id and self.pre_image == other.pre_image

    def __hash__(self):
        return hash((self.tx_id, self.pre_image))
