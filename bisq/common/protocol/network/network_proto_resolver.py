from abc import ABC, abstractmethod
import typing

from bisq.core.common.protocol.proto_resolver import ProtoResolver
from utils.clock import Clock
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope 
from bisq.core.common.protocol.network.network_payload import NetworkPayload
import proto.pb_pb2 as protobuf

class NetworkProtoResolver(ProtoResolver, ABC):
    @abstractmethod
    def from_proto(self, proto: typing.Union[protobuf.NetworkEnvelope, protobuf.StoragePayload, protobuf.StorageEntryWrapper]) -> typing.Union[NetworkEnvelope, NetworkPayload]:
        pass

    @abstractmethod
    def get_clock(self) -> Clock:
        pass