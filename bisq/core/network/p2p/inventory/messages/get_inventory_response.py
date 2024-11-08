from dataclasses import dataclass
from typing import Dict
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.inventory.model.inventory_item import InventoryItem
import proto.pb_pb2 as protobuf

@dataclass(eq=True, kw_only=True)
class GetInventoryResponse(NetworkEnvelope):
    inventory: Dict[InventoryItem, str]

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        map_proto = {item.value: value for item, value in self.inventory.items()}
        response = protobuf.GetInventoryResponse(inventory=map_proto) 
        envelope = self.get_network_envelope_builder()
        envelope.get_inventory_response.CopyFrom(response)
        return envelope

    @staticmethod
    def from_proto(cls, proto: protobuf.GetInventoryResponse, message_version: int):
        inventory = {}
        for key, value in proto.inventory.items():
            try:
                inventory_item = InventoryItem[key]
                inventory[inventory_item] = value
            except ValueError:
                pass  # Skip invalid enum values
        return GetInventoryResponse(message_version=message_version, inventory=inventory)