from dataclasses import dataclass, field
import hashlib
from bisq.core.common.protocol.network.network_payload import NetworkPayload
from bisq.core.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.common.used_for_trade_contract_json import UsedForTradeContractJson
import proto.pb_pb2 as protobuf

@dataclass(frozen=True)
class NodeAddress(PersistablePayload, NetworkPayload, UsedForTradeContractJson):
    host_name: str
    port: int
    address_prefix_hash: bytes = field(init=False, default=None)

    def __init__(self, host_name: str = None, port: int = None, full_address: str = None):
        if full_address:
            split = full_address.split(":")
            assert len(split) == 2, "fullAddress must contain ':'"
            self.host_name = split[0]
            self.port = int(split[1])
        else:
            self.host_name = host_name
            self.port = port
        self.address_prefix_hash = None

    def to_proto_message(self):
        return protobuf.NodeAddress(host_name=self.host_name, port=self.port)

    @staticmethod
    def from_proto(proto: protobuf.NodeAddress):
        return NodeAddress(host_name=proto.host_name, port=proto.port)

    def get_full_address(self):
        return f"{self.host_name}:{self.port}"

    def get_host_name_without_postfix(self):
        return self.host_name.replace(".onion", "")

    # tor v3 onions are too long to display for example in a table grid, so this convenience method
    # produces a display-friendly format which includes [first 7]..[last 7] characters.
    # tor v2 and localhost will be displayed in full, as they are 16 chars or less.
    def get_host_name_for_display(self):
        work = self.get_host_name_without_postfix()
        if len(work) > 16:
            return f"{work[:7]}..{work[-7:]}"
        return work

    # We use just a few chars from the full address to blur the potential receiver for sent network_messages
    def get_address_prefix_hash(self):
        if self.address_prefix_hash is None:
            full_address = self.get_full_address()
            self.address_prefix_hash = hashlib.sha256(full_address[:min(2, len(full_address))].encode()).digest()
        return self.address_prefix_hash

    def __str__(self):
        return self.get_full_address()