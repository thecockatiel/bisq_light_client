import uuid
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.locale.res import Res
import pb_pb2 as protobuf
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.governance.bond.bonded_asset import BondedAsset
from bisq.core.dao.state.model.governance.bonded_role_type import BondedRoleType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel


class Role(PersistablePayload, NetworkPayload, BondedAsset, ImmutableDaoStateModel):

    def __init__(
        self, name: str, link: str, bonded_role_type: BondedRoleType, uid: str = None
    ):
        if uid is None:
            uid = str(uuid.uuid4())
        self._uid = uid
        self.name = name  # Full name or nickname
        self.link = link  # GitHub account or forum account of user
        self.bonded_role_type = bonded_role_type

        # Only used as cache
        self._hash = get_sha256_ripemd160_hash(self.serialize_for_hash())  # transient

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return protobuf.Role(
            uid=self.uid,
            name=self.name,
            link=self.link,
            bonded_role_type=self.bonded_role_type.name,
        )

    @staticmethod
    def from_proto(proto: protobuf.Role):
        return Role(
            name=proto.name,
            link=proto.link,
            bonded_role_type=ProtoUtil.enum_from_proto(
                BondedRoleType, proto.bonded_role_type
            ),
            uid=proto.uid,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BondedAsset implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @property
    def hash(self):
        return self._hash

    @property
    def uid(self):
        return self._uid

    @property
    def display_string(self):
        return (
            Res.get("dao.bond.bondedRoleType." + self.bonded_role_type.name)
            + ": "
            + self.name
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def __eq__(self, other):
        if self is other:
            return True
        if other is None or not isinstance(other, Role):
            return False
        return (
            self.uid == other.uid
            and self.name == other.name
            and self.link == other.link
            and self.bonded_role_type.name == other.bonded_role_type.name
        )

    def __hash__(self):
        return hash((self.uid, self.name, self.link, self.bonded_role_type.name))

    def __str__(self):
        return (
            f"Role{{\n"
            f"     uid='{self.uid}',\n"
            f"     name='{self.name}',\n"
            f"     link='{self.link}',\n"
            f"     bondedRoleType='{self.bonded_role_type.name}'\n"
            f"}}"
        )
