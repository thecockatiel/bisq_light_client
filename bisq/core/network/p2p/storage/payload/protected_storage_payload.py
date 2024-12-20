from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Dict
from cryptography.hazmat.primitives.asymmetric import rsa

from bisq.common.protocol.network.network_payload import NetworkPayload

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
    def get_owner_pub_key(self) -> rsa.RSAPublicKey:
        """
        Used to check if the add or remove operation is permitted.
        Only the data owner can add or remove the data.
        OwnerPubKey must be equal to the ownerPubKey of the ProtectedStorageEntry.

        :return: The public key of the data owner.
        """
        pass

    @abstractmethod
    def get_extra_data_map(self) -> Optional[Dict[str, str]]:
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