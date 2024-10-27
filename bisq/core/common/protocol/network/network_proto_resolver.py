from abc import ABC, abstractmethod

from bisq.core.common.protocol.proto_resolver import ProtoResolver
from utils.clock import Clock
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope 
from bisq.core.common.protocol.network.network_payload import NetworkPayload
import proto.pb_pb2 as protobuf

class NetworkProtoResolver(ProtoResolver, ABC):
    @abstractmethod
    def from_proto_network_envelope(self, proto: protobuf.NetworkEnvelope) -> NetworkEnvelope:
        pass

    @abstractmethod
    def from_proto_storage_payload(self, proto: protobuf.StoragePayload) -> NetworkPayload:
        pass

    @abstractmethod
    def from_proto_storage_entry_wrapper(self, proto: protobuf.StorageEntryWrapper) -> NetworkPayload:
        pass

    @abstractmethod
    def get_clock(self) -> Clock:
        pass