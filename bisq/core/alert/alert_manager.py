import base64
from collections.abc import Collection
from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.log_setup import get_logger
from bisq.core.alert.alert import Alert
from bisq.core.network.p2p.storage.hash_map_changed_listener import (
    HashMapChangedListener,
)
from utils.data import SimpleProperty
from bisq.common.crypto.encryption import ECPrivkey, Encryption

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.user.user import User
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
        ProtectedStorageEntry,
    )


logger = get_logger(__name__)


class AlertManager:

    def __init__(
        self,
        p2p_service: "P2PService",
        key_ring: "KeyRing",
        user: "User",
        ignore_dev_msg: bool = False,
        use_dev_privilege_keys: bool = False,
    ):
        self.p2p_service = p2p_service
        self.key_ring = key_ring
        self.user = user
        self.alert_message_property = SimpleProperty["Alert"](None)

        # Pub key for developer global alert message
        self.alert_signing_key: Optional["ECPrivkey"] = None
        self.pub_key_as_hex: Optional[str] = None

        if not ignore_dev_msg:

            class ChangeListener(HashMapChangedListener):
                def on_added(
                    self_,
                    protected_storage_entries: Collection["ProtectedStorageEntry"],
                ):
                    for protected_storage_entry in protected_storage_entries:
                        protected_storage_payload = (
                            protected_storage_entry.protected_storage_payload
                        )
                        if isinstance(protected_storage_payload, Alert):
                            alert = protected_storage_payload
                            if self._verify_signature(alert):
                                self.alert_message_property.set(alert)

                def on_removed(
                    self_,
                    protected_storage_entries: Collection["ProtectedStorageEntry"],
                ):
                    for protected_storage_entry in protected_storage_entries:
                        protected_storage_payload = (
                            protected_storage_entry.protected_storage_payload
                        )
                        if isinstance(protected_storage_payload, Alert):
                            if self._verify_signature(protected_storage_payload):
                                self.alert_message_property.set(None)

            self.p2p_service.add_hash_set_changed_listener(ChangeListener())

        if use_dev_privilege_keys:
            self.pub_key_as_hex = DevEnv.DEV_PRIVILEGE_PUB_KEY
        else:
            self.pub_key_as_hex = (
                "036d8a1dfcb406886037d2381da006358722823e1940acc2598c844bbc0fd1026f"
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_alert_message_if_key_is_valid(
        self, alert: "Alert", priv_key_string: str
    ) -> bool:
        # If there is a previous message, remove it first
        if self.user.developers_alert is not None:
            self.remove_alert_message_if_key_is_valid(priv_key_string)

        if self._is_key_valid(priv_key_string):
            self._sign_and_add_signature_to_alert_message(alert)
            self.user.set_developers_alert(alert)
            result = self.p2p_service.add_protected_storage_entry(alert)
            if result:
                logger.debug(
                    f"Add alertMessage to network was successful. AlertMessage={alert}"
                )
            return True
        return False

    def remove_alert_message_if_key_is_valid(self, priv_key_string: str) -> bool:
        alert = self.user.developers_alert
        if self._is_key_valid(priv_key_string) and alert is not None:
            if self.p2p_service.remove_data(alert):
                logger.debug(
                    f"Remove alertMessage from network was successful. AlertMessage={alert}"
                )

            self.user.set_developers_alert(None)
            return True
        return False

    def _is_key_valid(self, priv_key_string: str) -> bool:
        try:
            self.alert_signing_key = Encryption.get_ec_private_key_from_int_hex_string(
                priv_key_string
            )
            return self.pub_key_as_hex == self.alert_signing_key.get_public_key_hex()
        except:
            return False

    def _sign_and_add_signature_to_alert_message(self, alert: "Alert") -> None:
        alert_message_as_hex = alert.message.encode("utf-8").hex()
        signature_as_base64 = base64.b64encode(
            self.alert_signing_key.sign_message(
                alert_message_as_hex,
                True,
            )
        ).decode("utf-8")
        alert.set_sig_and_pub_key(
            signature_as_base64,
            self.key_ring.signature_key_pair.public_key,
        )

    def _verify_signature(self, alert: "Alert") -> bool:
        alert_message_as_hex = alert.message.encode("utf-8").hex()
        try:
            Encryption.verify_ec_message_is_from_pubkey(
                alert_message_as_hex,
                alert.signature_as_base64,
                bytes.fromhex(self.pub_key_as_hex),
            )
            return True
        except:
            logger.warning("verify_signature failed")
            return False
