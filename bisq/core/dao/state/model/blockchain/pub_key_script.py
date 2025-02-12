from typing import TYPE_CHECKING, Optional
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.blockchain.script_type import ScriptType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.dao.node.full.rpc.dto.dto_pub_key_script import DtoPubKeyScript


class PubKeyScript(PersistablePayload, ImmutableDaoStateModel):

    def __init__(
        self,
        req_sigs: int,
        script_type: ScriptType,
        addresses: Optional[list[str]],
        asm: str,
        hex: str,
    ):
        self.req_sigs = req_sigs
        self.script_type = script_type
        self.addresses = tuple(addresses) if addresses else addresses
        self.asm = asm
        self.hex = hex

    @staticmethod
    def from_dto(dto: "DtoPubKeyScript"):
        return PubKeyScript(
            req_sigs=dto.req_sigs if dto.req_sigs is not None else 0,
            script_type=dto.type,
            addresses=dto.addresses,
            asm=dto.asm,
            hex=dto.hex,
        )

    def to_proto_message(self):
        builder = protobuf.PubKeyScript(
            req_sigs=self.req_sigs,
            script_type=self.script_type.to_proto_message(),
            addresses=self.addresses,
            asm=self.asm,
            hex=self.hex,
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.PubKeyScript):
        return PubKeyScript(
            req_sigs=proto.req_sigs,
            script_type=ScriptType.from_proto(proto.script_type),
            addresses=list(proto.addresses) if proto.addresses else None,
            asm=proto.asm,
            hex=proto.hex,
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, PubKeyScript):
            return False
        return (
            self.req_sigs == other.req_sigs
            and self.script_type.name == other.script_type.name
            and self.addresses == other.addresses
            and self.asm == other.asm
            and self.hex == other.hex
        )

    def __hash__(self):
        return hash(
            (
                self.req_sigs,
                self.script_type.name,
                self.addresses,
                self.asm,
                self.hex,
            )
        )
