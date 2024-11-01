from typing import TYPE_CHECKING, Set
from dataclasses import dataclass

from bisq.core.common.capabilities import Capabilities
from bisq.core.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.core.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.core.network.p2p.extended_data_size_permission import ExtendedDataSizePermission
from bisq.core.network.p2p.initial_data_response import InitialDataResponse
from bisq.core.network.p2p.peers.getdata.messages.get_updated_data_request import GetUpdatedDataRequest
from bisq.core.network.p2p.peers.getdata.messages.preliminary_get_data_request import PreliminaryGetDataRequest
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage
from bisq.logging import get_logger
import bisq.core.common.version as Version
from utils.formatting import readable_file_size
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry


logger = get_logger(__name__)


@dataclass(frozen=True)
class GetDataResponse(NetworkEnvelope, SupportedCapabilitiesMessage, ExtendedDataSizePermission, InitialDataResponse):
    # Set of ProtectedStorageEntry objects
    data_set: frozenset['ProtectedStorageEntry']
    
    # Set of PersistableNetworkPayload objects
    # We added that in v 0.6 and the from_proto code will create an empty set if it doesn't exist
    persistable_network_payload_set: frozenset['PersistableNetworkPayload']
    
    request_nonce: int
    is_get_updated_data_response: bool
    supported_capabilities: Capabilities
    
    # Added at v1.9.6
    was_truncated: bool

    def __init__(self,
                 data_set: Set['ProtectedStorageEntry'],
                 persistable_network_payload_set: Set['PersistableNetworkPayload'],
                 request_nonce: int,
                 is_get_updated_data_response: bool,
                 was_truncated: bool,
                 supported_capabilities: Capabilities = Capabilities.app,
                 message_version: int = Version.get_p2p_message_version()):
        super().__init__(message_version)
        self.data_set = frozenset(data_set)
        self.persistable_network_payload_set = frozenset(persistable_network_payload_set)
        self.request_nonce = request_nonce
        self.is_get_updated_data_response = is_get_updated_data_response
        self.was_truncated = was_truncated
        self.supported_capabilities = supported_capabilities

    def to_proto_network_envelope(self) -> NetworkEnvelope:
        get_data_response = protobuf.GetDataResponse()
        get_data_response.data_set = [entry.to_proto_message() for entry in self.data_set]
        get_data_response.persistable_network_payload_items = [payload.to_proto_message() for payload in self.persistable_network_payload_set]
        get_data_response.request_nonce = self.request_nonce
        get_data_response.is_get_updated_data_response = self.is_get_updated_data_response
        get_data_response.was_truncated = self.was_truncated
        get_data_response.supported_capabilities = self.supported_capabilities.to_int_list()

        network_envelope = self.get_network_envelope_builder()
        network_envelope.get_data_response.CopyFrom(get_data_response)

        logger.info(f"Sending a GetDataResponse with {readable_file_size(network_envelope.ByteSize())}")
        return network_envelope

    @staticmethod
    def from_proto(proto: 'protobuf.GetDataResponse', resolver: 'NetworkProtoResolver', message_version: int) -> 'GetDataResponse':
        was_truncated = proto.was_truncated
        logger.info(f"\n\n<< Received a GetDataResponse with {readable_file_size(proto.ByteSize())} {' (still data missing)' if was_truncated else ' (all data received)'}\n")
        data_set = {resolver.from_proto(entry) for entry in proto.data_set}
        persistable_network_payload_set = {resolver.from_proto(e) for e in proto.persistable_network_payload_items}
        return GetDataResponse(
            data_set,
            persistable_network_payload_set,
            proto.request_nonce,
            proto.is_get_updated_data_response,
            was_truncated,
            Capabilities.from_int_list(proto.supported_capabilities),
            message_version
        )

    def associated_request(self) -> type:
        return GetUpdatedDataRequest if self.is_get_updated_data_response else PreliminaryGetDataRequest