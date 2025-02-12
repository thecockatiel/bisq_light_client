import uuid
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.bond.bonded_asset import BondedAsset
from utils.preconditions import check_argument
import pb_pb2 as protobuf


class MyReputation(PersistablePayload, NetworkPayload, BondedAsset):
    """
    MyReputation is persisted locally and carries the private salt data. In contrast to Reputation which is the public
    data everyone can derive from the blockchain data (hash in opReturn).
    """

    def __init__(self, salt: bytes, uid: str = None):
        if uid is None:
            uid = str(uuid.uuid4())
        # Uid is needed to be sure that 2 objects with the same salt are kept separate.
        self._uid = uid
        self.salt = salt
        check_argument(len(salt) <= 20, "salt must not be longer than 20 bytes")
        # Not persisted as it is derived from salt. Stored for caching purpose only.
        self._hash = get_sha256_ripemd160_hash(self.salt)  # transient

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> protobuf.MyReputation:
        return protobuf.MyReputation(uid=self.uid, salt=self.salt)

    @staticmethod
    def from_proto(proto: protobuf.MyReputation) -> "MyReputation":
        return MyReputation(salt=proto.salt, uid=proto.uid)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BondedAsset implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def uid(self) -> str:
        return bytes_as_hex_string(self.hash)

    @property
    def hash(self):
        return self._hash

    @property
    def display_string(self) -> str:
        return self.uid

    def __eq__(self, other):
        if not isinstance(other, MyReputation):
            return False
        return self.uid == other.uid and self.salt == other.salt

    def __hash__(self):
        return hash((self.uid, self.salt))

    def __str__(self):
        return (
            f"MyReputation{{\n"
            f"     uid={self.uid}\n"
            f"     salt={bytes_as_hex_string(self.salt)}\n"
            f"     hash={bytes_as_hex_string(self.hash)}\n"
            f"}}"
        )
