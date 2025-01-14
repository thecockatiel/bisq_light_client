import base64
from datetime import timedelta
from typing import TYPE_CHECKING, Optional, TypeVar, Generic, List
from abc import ABC, abstractmethod

from bisq.common.crypto.encryption import Encryption, ECPrivkey
from bisq.common.crypto.sig import Sig, dsa
from bisq.common.app.dev_env import DevEnv
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.storage.hash_map_changed_listener import HashMapChangedListener
from bisq.core.support.dispute.agent.dispute_agent import DisputeAgent
from utils.data import ObservableMap

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.user.user import User
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import ProtectedStorageEntry
    from bisq.core.support.dispute.agent.dispute_agent_service import DisputeAgentService

T = TypeVar('T', bound='DisputeAgent')

logger = get_logger(__name__)

# TODO: cryptography usages needs double check.

class DisputeAgentManager(Generic[T], ABC):
    REPUBLISH_MILLIS: int = DisputeAgent.TTL // 2
    RETRY_REPUBLISH_SEC: int = 5
    REPEATED_REPUBLISH_AT_STARTUP_SEC: int = 60

    def __init__(self, 
                 key_ring: 'KeyRing',
                 dispute_agent_service: 'DisputeAgentService[T]',
                 user: 'User',
                 filter_manager: 'FilterManager',
                 use_dev_privilege_keys: bool):
        self.public_keys: list[str] = [DevEnv.DEV_PRIVILEGE_PUB_KEY] if use_dev_privilege_keys else self.get_pub_key_list()
        self.key_ring = key_ring
        self.dispute_agent_service = dispute_agent_service
        self.user = user
        self.filter_manager = filter_manager
        self.observable_map: ObservableMap["NodeAddress", T] = ObservableMap()
        self.persisted_accepted_dispute_agents: list[T] = []
        self.republish_timer: Optional["Timer"] = None
        self.retry_republish_timer: Optional["Timer"] = None


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Abstract methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def get_pub_key_list(self) -> List[str]:
        pass

    @abstractmethod
    def is_expected_instance(self, data: 'ProtectedStorageEntry') -> bool:
        pass

    @abstractmethod
    def add_accepted_dispute_agent_to_user(self, dispute_agent: T) -> None:
        pass

    @abstractmethod
    def get_registered_dispute_agent_from_user(self) -> T:
        pass

    @abstractmethod
    def clear_accepted_dispute_agents_at_user(self) -> None:
        pass

    @abstractmethod
    def get_accepted_dispute_agents_from_user(self) -> List[T]:
        pass

    @abstractmethod
    def remove_accepted_dispute_agent_from_user(self, data: 'ProtectedStorageEntry') -> None:
        pass

    @abstractmethod
    def set_registered_dispute_agent_at_user(self, dispute_agent: T) -> None:
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self) -> None:
        class DisputeAgentHashMapListener(HashMapChangedListener):
            def on_added(self_, protected_storage_entries):
                for entry in protected_storage_entries:
                    if self.is_expected_instance(entry):
                        self.update_map()

            def on_removed(self_, protected_storage_entries):
                for entry in protected_storage_entries:
                    if self.is_expected_instance(entry):
                        self.update_map()
                        self.remove_accepted_dispute_agent_from_user(entry)
        self.dispute_agent_service.add_hash_set_changed_listener(DisputeAgentHashMapListener())

        self.persisted_accepted_dispute_agents = list(self.get_accepted_dispute_agents_from_user())
        self.clear_accepted_dispute_agents_at_user()

        registered_agent = self.get_registered_dispute_agent_from_user()
        if registered_agent is not None:
            p2p_service = self.dispute_agent_service.p2p_service
            if p2p_service.is_bootstrapped:
                self.start_republish_dispute_agent()
            else:
                class Listener(BootstrapListener):
                    def on_data_received(self_):
                        self.start_republish_dispute_agent()
                p2p_service.add_p2p_service_listener(Listener())

        self.filter_manager.filter_property.add_listener(
            lambda e: self.update_map()
        )

        self.update_map()

    def shut_down(self) -> None:
        self.stop_republish_timer()
        self.stop_retry_republish_timer()

    def start_republish_dispute_agent(self) -> None:
        if self.republish_timer is None:
            self.republish_timer = UserThread.run_periodically(self.republish, timedelta(milliseconds=DisputeAgentManager.REPUBLISH_MILLIS))
            UserThread.run_after(self.republish, timedelta(seconds=DisputeAgentManager.REPEATED_REPUBLISH_AT_STARTUP_SEC))
            self.republish()

    def update_map(self) -> None:
        dispute_agents = self.dispute_agent_service.get_dispute_agents()
        self.observable_map.clear()
        
        filtered = {}
        for agent in dispute_agents.values():
            pub_key_hex = agent.registration_pub_key.hex()
            is_in_public_key_list = self.is_public_key_in_list(pub_key_hex)
            
            if not is_in_public_key_list:
                if DevEnv.DEV_PRIVILEGE_PUB_KEY == pub_key_hex:
                    logger.info(
                        f"We got the DEV_PRIVILEGE_PUB_KEY in our list of publicKeys. "
                        f"RegistrationPubKey={agent.registration_pub_key.hex()}, "
                        f"nodeAddress={agent.node_address.get_full_address()}"
                    )
                else:
                    logger.warning(
                        f"We got an disputeAgent which is not in our list of publicKeys. "
                        f"RegistrationPubKey={agent.registration_pub_key.hex()}, "
                        f"nodeAddress={agent.node_address.get_full_address()}"
                    )
            
            is_sig_valid = self.verify_signature(
                agent.pub_key_ring.signature_pub_key,
                agent.registration_pub_key,
                agent.registration_signature
            )
            
            if not is_sig_valid:
                logger.warning(f"Sig check for disputeAgent failed. DisputeAgent={agent}")
            
            if is_in_public_key_list and is_sig_valid:
                filtered[agent.node_address] = agent

        self.observable_map.update(filtered)
        for agent in self.observable_map.values():
            self.add_accepted_dispute_agent_to_user(agent)

    def add_dispute_agent(self, dispute_agent: T, result_handler: "ResultHandler", error_message_handler: "ErrorMessageHandler") -> None:
        self.set_registered_dispute_agent_at_user(dispute_agent)
        self.observable_map[dispute_agent.node_address] = dispute_agent
        
        def on_success():
            logger.info("DisputeAgent successfully saved in P2P network")
            result_handler()
            
            if len(self.observable_map) > 0:
                UserThread.run_after(
                    self.update_map,
                    timedelta(milliseconds=100)
                )
        
        self.dispute_agent_service.add_dispute_agent(
            dispute_agent,
            on_success,
            error_message_handler
        )

    def remove_dispute_agent(self, result_handler: "ResultHandler", error_message_handler: "ErrorMessageHandler") -> None:
        registered_dispute_agent = self.get_registered_dispute_agent_from_user()
        if registered_dispute_agent is not None:
            self.set_registered_dispute_agent_at_user(None)
            del self.observable_map[registered_dispute_agent.node_address]
            
            def on_success():
                logger.debug("DisputeAgent successfully removed from P2P network")
                result_handler()
            
            self.dispute_agent_service.remove_dispute_agent(
                registered_dispute_agent,
                on_success,
                error_message_handler
            )

    # A protected key is handed over to selected disputeAgents for registration.
    # An invited disputeAgent will sign at registration his storageSignaturePubKey with that protected key and attach the signature and pubKey to his data.
    # Other users will check the signature with the list of public keys hardcoded in the app.
    def sign_storage_signature_pub_key(self, key: ECPrivkey):
        key_to_sign= Sig.get_public_key_bytes(self.key_ring.pub_key_ring.signature_pub_key)
        return key.sign_message(key_to_sign) # passes LowRSigningKey tests.
    
    def get_registration_key(self, priv_key_big_int_string: str):
        try:
            return Encryption.get_ec_private_key_from_int_hex_string(priv_key_big_int_string)
        except:
            return None
        
    def is_public_key_in_list(self, pub_key_hex: str) -> bool:
        return pub_key_hex in self.public_keys

    def is_agent_available_for_language(self, language_code: str) -> bool:
        return any(language_code in agent.language_codes 
                  for agent in self.observable_map.values())

    def get_dispute_agent_languages(self, node_addresses: List["NodeAddress"]) -> List[str]:
        languages = set()
        for agent in self.observable_map.values():
            if agent.node_address in node_addresses:
                languages.update(agent.language_codes)
        return list(languages)

    def get_dispute_agent_by_node_address(self, node_address: "NodeAddress") -> Optional[T]:
        return self.observable_map.get(node_address, None)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def republish(self) -> None:
        registered_dispute_agent = self.get_registered_dispute_agent_from_user()
        if registered_dispute_agent is not None:
            def on_error(error_message: str):
                if self.retry_republish_timer is None:
                    def retry():
                        self.stop_retry_republish_timer()
                        self.republish()
                    self.retry_republish_timer = UserThread.run_periodically(
                        retry,
                        timedelta(seconds=DisputeAgentManager.RETRY_REPUBLISH_SEC)
                    )

            self.add_dispute_agent(
                registered_dispute_agent,
                self.update_map,
                on_error
            )

    def verify_signature(self, storage_signature_pub_key: dsa.DSAPublicKey, registration_pub_key_ec: bytes, signature_base64: str) -> bool:
        try:
            key_to_sign_as_hex = Sig.get_public_key_as_hex_string(storage_signature_pub_key)
            key = Encryption.get_ec_public_key_from_bytes(registration_pub_key_ec)
            return key.verify_message_hash(base64.b64decode(signature_base64), key_to_sign_as_hex)
        except:
            logger.warning("verify_signature failed")
            return False

    def stop_retry_republish_timer(self) -> None:
        if self.retry_republish_timer is not None:
            self.retry_republish_timer.stop()
            self.retry_republish_timer = None

    def stop_republish_timer(self) -> None:
        if self.republish_timer is not None:
            self.republish_timer.stop()
            self.republish_timer = None

