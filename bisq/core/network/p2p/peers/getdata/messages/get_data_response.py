from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

from bisq.common.capabilities import Capabilities
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.core.network.p2p.extended_data_size_permission import ExtendedDataSizePermission
from bisq.core.network.p2p.initial_data_response import InitialDataResponse
from bisq.core.network.p2p.peers.getdata.messages.get_updated_data_request import GetUpdatedDataRequest
from bisq.core.network.p2p.peers.getdata.messages.preliminary_get_data_request import PreliminaryGetDataRequest
from bisq.core.network.p2p.supported_capabilities_message import SupportedCapabilitiesMessage

from utils.data import raise_required
from utils.formatting import readable_file_size
import pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.core.network.p2p.storage.payload.persistable_network_payload import PersistableNetworkPayload
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry


@dataclass
class GetDataResponse(NetworkEnvelope, SupportedCapabilitiesMessage, ExtendedDataSizePermission, InitialDataResponse):
    # Set of ProtectedStorageEntry objects
    data_set: frozenset['ProtectedStorageEntry'] = field(default_factory=frozenset)
    
    # Set of PersistableNetworkPayload objects
    # We added that in v 0.6 and the from_proto code will create an empty set if it doesn't exist
    persistable_network_payload_set: frozenset['PersistableNetworkPayload'] = field(default_factory=raise_required)
    
    request_nonce: int = field(default_factory=raise_required)
    is_get_updated_data_response: bool = field(default_factory=raise_required)
    supported_capabilities: Capabilities = field(default_factory=lambda: Capabilities.app)
    
    # Added at v1.9.6
    was_truncated: bool = field(default_factory=raise_required)

    def __post_init__(self):
        self.logger = get_ctx_logger(__name__)

    def to_proto_network_envelope(self) -> protobuf.NetworkEnvelope:
        get_data_response = protobuf.GetDataResponse(
            data_set=[entry.to_proto_message() for entry in self.data_set],
            persistable_network_payload_items = [payload.to_proto_message() for payload in self.persistable_network_payload_set],
            request_nonce = self.request_nonce,
            is_get_updated_data_response = self.is_get_updated_data_response,
            was_truncated = self.was_truncated,
            supported_capabilities = self.supported_capabilities.to_int_list()
        )

        network_envelope = self.get_network_envelope_builder()
        network_envelope.get_data_response.CopyFrom(get_data_response)

        self.logger.info(f"Sending a GetDataResponse with {readable_file_size(network_envelope.ByteSize())}")
        return network_envelope

    @staticmethod
    def from_proto(proto: 'protobuf.GetDataResponse', resolver: 'NetworkProtoResolver', message_version: int) -> 'GetDataResponse':
        was_truncated = proto.was_truncated
        logger = get_ctx_logger(__name__)
        logger.info(f"\n\n<< Received a GetDataResponse with {readable_file_size(proto.ByteSize())} {' (still data missing)' if was_truncated else ' (all data received)'}\n")
        
        data_set = frozenset(
            resolver.from_proto(entry) for entry in proto.data_set
        )
        
        persistable_network_payload_set = frozenset(
            resolver.from_proto(payload) for payload in proto.persistable_network_payload_items
        )

        return GetDataResponse(
            message_version=message_version,
            data_set=data_set,
            persistable_network_payload_set=persistable_network_payload_set,
            request_nonce=proto.request_nonce,
            is_get_updated_data_response=proto.is_get_updated_data_response,
            supported_capabilities=Capabilities.from_int_list(proto.supported_capabilities),
            was_truncated=was_truncated,
        )

    def associated_request(self) -> type:
        return GetUpdatedDataRequest if self.is_get_updated_data_response else PreliminaryGetDataRequest