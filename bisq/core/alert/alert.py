from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import timedelta
from bisq.core.common.crypto.sig import Sig, dsa
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
    ProtectedStoragePayload,
)
from bisq.core.common.protocol.network.get_data_response_priority import (
    GetDataResponsePriority,
)
import proto.pb_pb2 as protobuf


class Alert(ProtectedStoragePayload, ExpirablePayload):
    TTL: int = timedelta(days=90).total_seconds() * 1000  # milliseconds

    message: str
    is_update_info: bool
    is_pre_release_info: bool
    version: str

    owner_pub_key_bytes: Optional[bytes]
    signature_as_base64: Optional[str]
    owner_pub_key: Optional[Any] = None  # PublicKey equivalent
    extra_data_map: Optional[Dict[str, str]] = None

    def __init__(
        self,
        message: str,
        is_update_info: bool,
        is_pre_release_info: bool,
        version: str,
        owner_pub_key_bytes: bytes = None,
        signature_as_base64: str = None,
        extra_data_map: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__()
        self.message = message
        self.is_update_info = is_update_info
        self.is_pre_release_info = is_pre_release_info
        self.version = version
        self.owner_pub_key_bytes = owner_pub_key_bytes
        self.signature_as_base64 = signature_as_base64
        self.extra_data_map = extra_data_map

        if self.owner_pub_key_bytes:
            self.owner_pub_key = Sig.get_public_key_from_bytes(self.owner_pub_key_bytes)

    def to_proto_message(self) -> "protobuf.StoragePayload":
        assert (
            self.owner_pub_key_bytes is not None
        ), "storagePublicKeyBytes must not be null"
        assert (
            self.signature_as_base64 is not None
        ), "signatureAsBase64 must not be null"

        alert = protobuf.Alert(
            message=self.message,
            is_update_info=self.is_update_info,
            is_pre_release_info=self.is_pre_release_info,
            version=self.version,
            owner_pub_key_bytes=self.owner_pub_key_bytes,
            signature_as_base64=self.signature_as_base64,
        )

        if self.extra_data_map:
            alert.extra_data.update(self.extra_data_map)

        return protobuf.StoragePayload(alert=alert)

    @staticmethod
    def from_proto(proto: "protobuf.Alert") -> Optional["Alert"]:
        # We got in dev testing sometimes an empty protobuf Alert. Not clear why that happened but as it causes an
        # exception and corrupted user db file we prefer to set it to null.
        if not proto.signature_as_base64:
            return None

        return Alert(
            message=proto.message,
            is_update_info=proto.is_update_info,
            is_pre_release_info=proto.is_pre_release_info,
            version=proto.version,
            owner_pub_key_bytes=bytes(proto.owner_pub_key_bytes),
            signature_as_base64=proto.signature_as_base64,
            extra_data_map=dict(proto.extra_data) if proto.extra_data else None,
        )

    def get_get_data_response_priority(self) -> GetDataResponsePriority:
        return GetDataResponsePriority.HIGH

    def get_ttl(self) -> int:
        return self.TTL

    def set_sig_and_pub_key(
        self, signature_as_base64: str, owner_pub_key: dsa.DSAPublicKey
    ) -> None:
        self.signature_as_base64 = signature_as_base64
        self.owner_pub_key = owner_pub_key
        self.owner_pub_key_bytes = Sig.get_public_key_bytes(owner_pub_key)

    def is_new_version(self) -> bool:
        # TODO:
        return False

    def is_software_update_notification(self) -> bool:
        return self.is_update_info or self.is_pre_release_info

    def can_show_popup(self) -> bool:
        # TODO:
        return False

    def show_again_key(self) -> str:
        return f"Update_{self.version}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Alert):
            return False
        return (
            self.message == other.message
            and self.version == other.version
            and self.is_update_info == other.is_update_info
            and self.is_pre_release_info == other.is_pre_release_info
            and self.owner_pub_key_bytes == other.owner_pub_key_bytes
            and self.signature_as_base64 == other.signature_as_base64
            and self.extra_data_map == other.extra_data_map
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.message,
                self.version,
                self.is_update_info,
                self.is_pre_release_info,
                self.owner_pub_key_bytes,
                self.signature_as_base64,
            )
        )
