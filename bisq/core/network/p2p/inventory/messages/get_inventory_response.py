from dataclasses import dataclass, field
from typing import Dict
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.network.p2p.inventory.model.inventory_item import InventoryItem
import pb_pb2 as protobuf
from utils.data import raise_required
from utils.pb_helper import map_to_stable_extra_data, stable_extra_data_to_map


@dataclass(eq=True)
class GetInventoryResponse(NetworkEnvelope):
    inventory: Dict[InventoryItem, str] = field(default_factory=raise_required)

    def to_proto_message(self):
        # For protobuf we use a map with a string key
        return protobuf.GetInventoryResponse(
            inventory=map_to_stable_extra_data({item.key: value for item, value in self.inventory.items()})
        )

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        envelope = self.get_network_envelope_builder()
        envelope.get_inventory_response.CopyFrom(self.to_proto_message())
        return envelope

    @staticmethod
    def from_proto(proto: protobuf.GetInventoryResponse, message_version: int):
        inventory: dict[InventoryItem, str] = {}
        for key, value in stable_extra_data_to_map(proto.inventory).items():
            try:
                inventory_item = InventoryItem.from_key(key)
                inventory[inventory_item] = value
            except ValueError:
                pass  # Skip invalid enum values
        return GetInventoryResponse(
            message_version=message_version, inventory=inventory
        )
