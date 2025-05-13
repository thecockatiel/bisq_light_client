from typing import TYPE_CHECKING, Optional, Any
from datetime import timedelta
from bisq.common.crypto.sig import Sig, DSA
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import (
    ProtectedStoragePayload,
)
from bisq.common.protocol.network.get_data_response_priority import (
    GetDataResponsePriority,
)
from bisq.common.version import Version
import pb_pb2 as protobuf
from bisq.common.protocol.proto_util import ProtoUtil

if TYPE_CHECKING:
    from bisq.core.user.preferences import Preferences


class Alert(ProtectedStoragePayload, ExpirablePayload):
    TTL: int = int(timedelta(days=90).total_seconds() * 1000)  # milliseconds

    message: str
    is_update_info: bool
    is_pre_release_info: bool
    version: str

    owner_pub_key_bytes: Optional[bytes]
    signature_as_base64: Optional[str]
    owner_pub_key: Optional[Any] = None  # PublicKey equivalent
    extra_data_map: Optional[dict[str, str]] = None

    def __init__(
        self,
        message: str,
        is_update_info: bool,
        is_pre_release_info: bool,
        version: str,
        owner_pub_key_bytes: bytes = None,
        signature_as_base64: str = None,
        extra_data_map: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__()
        self.message = message
        self.is_update_info = is_update_info
        self.is_pre_release_info = is_pre_release_info
        self.version = version
        self.owner_pub_key_bytes = owner_pub_key_bytes
        self.signature_as_base64 = signature_as_base64
        self.extra_data_map = extra_data_map
        self._owner_pub_key = None

    @property
    def owner_pub_key(self) -> "DSA.DsaKey":
        if self._owner_pub_key is None:
            self._owner_pub_key = Sig.get_public_key_from_bytes(self.owner_pub_key_bytes)
        return self._owner_pub_key

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
            alert.extra_data.extend(ProtoUtil.to_string_map_entry_list(self.extra_data_map))

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
            owner_pub_key_bytes=proto.owner_pub_key_bytes,
            signature_as_base64=proto.signature_as_base64,
            extra_data_map=ProtoUtil.to_string_map(proto.extra_data),
        )

    def get_data_response_priority(self) -> GetDataResponsePriority:
        return GetDataResponsePriority.HIGH

    def get_ttl(self) -> int:
        return self.TTL

    def set_sig_and_pub_key(
        self, signature_as_base64: str, owner_pub_key: "DSA.DsaKey"
    ) -> None:
        self.signature_as_base64 = signature_as_base64
        self._owner_pub_key = owner_pub_key
        self.owner_pub_key_bytes = Sig.get_public_key_bytes(owner_pub_key)

    def is_new_version(self, preferences: "Preferences") -> bool:
        # regular release: always notify user
        # pre-release: if user has set preference to receive pre-release notification
        if self.is_update_info or (self.is_pre_release_info and preferences.is_notify_on_pre_release()):
            return Version.is_new_version(self.version)
        return False

    def is_software_update_notification(self) -> bool:
        return self.is_update_info or self.is_pre_release_info

    def can_show_popup(self, preferences: "Preferences") -> bool:
        # only show popup if its version is newer than current
        # and only if user has not checked "don't show again"
        return self.is_new_version(preferences) and not preferences.show_again(self.show_again_key())
        
    def show_again_key(self) -> str:
        return f"Update_{self.version}"
    
    def get_extra_data_map(self):
        return self.extra_data_map
    
    def get_owner_pub_key_bytes(self):
        return self.owner_pub_key_bytes

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
