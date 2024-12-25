from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.encryption import PUBLIC_KEY_TYPES
from bisq.common.protocol.network.network_payload import NetworkPayload
from google.protobuf import message as Message
import proto.pb_pb2 as protobuf

if TYPE_CHECKING:
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver

class ProtectedStoragePayload(NetworkPayload, ABC):
    """
    Messages which support ownership protection (using signatures) and a time to live.

    Implementations:
    - io.bisq.alert.Alert
    - io.bisq.arbitration.Arbitrator
    - io.bisq.trade.offer.OfferPayload
    """

    @abstractmethod
    def get_owner_pub_key(self) -> PUBLIC_KEY_TYPES:
        """
        Used to check if the add or remove operation is permitted.
        Only the data owner can add or remove the data.
        OwnerPubKey must be equal to the ownerPubKey of the ProtectedStorageEntry.

        :return: The public key of the data owner.
        """
        pass

    @abstractmethod
    def get_extra_data_map(self) -> Optional[dict[str, str]]:
        """
        Should be used only in emergency cases if data needs to be added without breaking
        backward compatibility at the P2P network storage checks.
        The hash of the object will verify if the data is valid. Any new field in a class
        would break that hash and therefore break the storage mechanism.

        :return: A dictionary of extra data.
        """
        pass

    @staticmethod
    def from_proto(storage_payload, network_proto_resolver: 'NetworkProtoResolver') -> 'ProtectedStoragePayload':
        return network_proto_resolver.from_proto(storage_payload)
    

def wrap_in_storage_payload(message: Message):
    """Wraps any valid message into StoragePayload by determining correct field at runtime"""
    
    if isinstance(message, protobuf.StoragePayload):
        return message
    
    # Get the descriptor for StoragePayload
    storage_desc = protobuf.StoragePayload.DESCRIPTOR
    oneof = storage_desc.oneofs_by_name['message']
    
    # Find matching field for the message type
    msg_type = type(message)
    for field in oneof.fields:
        if field.message_type.full_name == msg_type.DESCRIPTOR.full_name:
            kwargs = {field.name: message}
            return protobuf.StoragePayload(**kwargs)
            
    raise ValueError(f"Message type {msg_type.__name__} not found in StoragePayload")
