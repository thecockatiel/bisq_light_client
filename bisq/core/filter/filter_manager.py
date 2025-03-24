from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional, Collection
from abc import ABC, abstractmethod
import base64

from bisq.common.app.dev_env import DevEnv
from bisq.common.config.config import Config
from bisq.common.config.config_file_editor import ConfigFileEditor
from bisq.common.crypto.encryption import Encryption, ECPrivkey, ECPubkey
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.proof_of_work_service_instance_holder import (
    pow_service_for_version,
)
from bisq.common.setup.log_setup import get_logger
from bisq.core.provider.price_feed_node_address_provider import (
    PriceFeedNodeAddressProvider,
)
from utils.preconditions import check_argument
from bisq.core.locale.res import Res
from bisq.core.filter.filter import Filter
from bisq.core.network.p2p.storage.hash_map_changed_listener import (
    HashMapChangedListener,
)
from utils.data import SimpleProperty
from bisq.common.version import Version
from bisq.core.network.p2p.p2p_service_listener import P2PServiceListener

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.payment.payload.payment_method import PaymentMethod
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.network.ban_filter import BanFilter
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.user.user import User
    from bisq.core.network.p2p.storage.payload.protected_storage_entry import (
        ProtectedStorageEntry,
    )

# NOTE: removed preferences as not needed

logger = get_logger(__name__)


# TODO: cryptography usages needs double check.
class FilterManager:
    # Class constants
    BANNED_PRICE_RELAY_NODES = "bannedPriceRelayNodes"
    BANNED_SEED_NODES = "bannedSeedNodes"
    BANNED_BTC_NODES = "bannedBtcNodes"
    FILTER_PROVIDED_SEED_NODES = "filterProvidedSeedNodes"
    FILTER_PROVIDED_BTC_NODES = "filterProvidedBtcNodes"

    class Listener(Callable[["Filter"], None], ABC):
        @abstractmethod
        def on_filter_added(self, filter: "Filter"):
            pass

        def __call__(self, filter: "Filter"):
            self.on_filter_added(filter)

    def __init__(
        self,
        p2p_service: "P2PService",
        key_ring: "KeyRing",
        user: "User",
        config: "Config",
        price_feed_node_address_provider: "PriceFeedNodeAddressProvider",
        ban_filter: "BanFilter",
        ignore_dev_msg: bool = None,
        use_dev_privilege_keys: bool = None,
    ):
        if ignore_dev_msg is None:
            ignore_dev_msg = config.ignore_dev_msg
        if use_dev_privilege_keys is None:
            use_dev_privilege_keys = config.use_dev_privilege_keys

        self._p2p_service = p2p_service
        self._key_ring = key_ring
        self._user = user
        self._config = config
        self._config_file_editor = ConfigFileEditor(config.config_file)
        self._price_feed_node_address_provider = price_feed_node_address_provider
        self._ignore_dev_msg: bool = ignore_dev_msg

        self.filter_property: SimpleProperty[Optional["Filter"]] = SimpleProperty(None)
        self.listeners: set["FilterManager.Listener"] = set()
        self.invalid_filters: set["Filter"] = set()
        self.filter_warning_handler: Optional[Callable[[str], None]] = None
        self.filter_signing_key: Optional[ECPrivkey] = None

        self.public_keys: list[str] = []

        if use_dev_privilege_keys:
            self.public_keys = DevEnv.get_dev_privilege_pub_keys()
        else:
            # TODO: Keep this updated with java impl
            self.public_keys = [
                "0358d47858acdc41910325fce266571540681ef83a0d6fedce312bef9810793a27",
                "029340c3e7d4bb0f9e651b5f590b434fecb6175aeaa57145c7804ff05d210e534f",
                "034dc7530bf66ffd9580aa98031ea9a18ac2d269f7c56c0e71eca06105b9ed69f9",
            ]

        ban_filter.set_banned_node_predicate(self.is_node_address_banned_from_network)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_all_services_initialized(self):
        if self._ignore_dev_msg:
            return

        storage_entries = self._p2p_service.p2p_data_storage.map.values()
        for entry in storage_entries:
            payload = entry.protected_storage_payload
            if isinstance(payload, Filter):
                self.on_filter_added_from_network(payload)

        # On mainNet we expect to have received a filter object, if not show a popup to the user to inform the
        # Bisq devs.
        if (
            self._config.base_currency_network.is_mainnet()
            and self.get_filter() is None
            and self.filter_warning_handler is not None
        ):
            self.filter_warning_handler(Res.get("popup.warning.noFilter"))

        # Add hash set changed listener
        class HashSetListener(HashMapChangedListener):
            def __init__(self, outer: "FilterManager"):
                self.outer = outer

            def on_added(
                self, protected_storage_entries: Collection["ProtectedStorageEntry"]
            ):
                for entry in protected_storage_entries:
                    payload = entry.protected_storage_payload
                    if isinstance(payload, Filter):
                        self.outer.on_filter_added_from_network(payload)

            def on_removed(
                self, protected_storage_entries: Collection["ProtectedStorageEntry"]
            ):
                for entry in protected_storage_entries:
                    payload = entry.protected_storage_payload
                    if isinstance(payload, Filter):
                        self.outer.on_filter_removed_from_network(payload)

        self._p2p_service.add_hash_set_changed_listener(HashSetListener(self))

        # Add P2P service listener
        class ServiceListener(P2PServiceListener):
            def __init__(self, outer: "FilterManager"):
                self.outer = outer

            def on_data_received(self):
                # We should have received all data at that point and if the filters were not set we
                # clean up the persisted banned nodes in the options file as it might be that we missed the filter
                # remove message if we have not been online.
                if self.outer.filter_property.get() is None:
                    self.outer.clear_banned_nodes()

            def on_no_seed_node_available(self):
                pass

            def on_no_peers_available(self):
                pass

            def on_updated_data_received(self):
                pass

            def on_tor_node_ready(self):
                pass

            def on_hidden_service_published(self):
                pass

            def on_setup_failed(self, throwable):
                pass

            def on_request_custom_bridges(self):
                pass

        self._p2p_service.add_p2p_service_listener(ServiceListener(self))

    def set_filter_warning_handler(self, filter_warning_handler: Callable[[str], None]):
        self.filter_warning_handler = filter_warning_handler

        def on_filter(filter: "Filter"):
            if filter is not None and self.filter_warning_handler is not None:
                if filter.seed_nodes:
                    logger.info(
                        f"One of the seed nodes got banned. {filter.seed_nodes}"
                    )
                    # Let's keep that more silent. Might be used in case a node is unstable and we don't want to confuse users.
                    # filter_warning_handler(Res.get("popup.warning.nodeBanned", Res.get("popup.warning.seed")))

                if filter.price_relay_nodes:
                    logger.info(
                        f"One of the price relay nodes got banned. {filter.price_relay_nodes}"
                    )
                    # Let's keep that more silent. Might be used in case a node is unstable and we don't want to confuse users.
                    # filter_warning_handler(Res.get("popup.warning.nodeBanned", Res.get("popup.warning.priceRelay")))

                if self.require_update_to_new_version_for_trading():
                    self.filter_warning_handler(
                        Res.get("popup.warning.mandatoryUpdate.trading")
                    )

                if self.require_update_to_new_version_for_dao():
                    self.filter_warning_handler(
                        Res.get("popup.warning.mandatoryUpdate.dao")
                    )

                if filter.disable_dao:
                    self.filter_warning_handler(Res.get("popup.warning.disable.dao"))

        self.add_listener(on_filter)

    def is_privileged_dev_pub_key_banned(self, pub_key_as_hex: str) -> bool:
        filter = self.get_filter()
        if filter is None:
            return False
        return pub_key_as_hex in filter.banned_privileged_dev_pub_keys

    def can_add_dev_filter(self, priv_key_string: str) -> bool:
        if not priv_key_string:
            return False

        if not self.is_valid_dev_privilege_key(priv_key_string):
            logger.warning("Key is invalid")
            return False

        private_key = self.to_ec_key(priv_key_string)
        pub_key_as_hex = self.get_pub_key_as_hex(private_key)

        if self.is_privileged_dev_pub_key_banned(pub_key_as_hex):
            logger.warning("Pub key is banned")
            return False

        return True

    def get_signer_pub_key_as_hex(self, priv_key_string: str) -> str:
        private_key = self.to_ec_key(priv_key_string)
        return self.get_pub_key_as_hex(private_key)

    def add_dev_filter(self, filter_without_sig: "Filter", priv_key_string: str):
        self.set_filter_signing_key(priv_key_string)
        signature_as_base64 = self.get_signature(filter_without_sig)
        filter_with_sig = Filter.clone_with_sig(filter_without_sig, signature_as_base64)
        self._user.set_developers_filter(filter_with_sig)

        self._p2p_service.add_protected_storage_entry(filter_with_sig)

        # Cleanup potential old filters created in the past with same priv key
        for filter in self.invalid_filters.copy():
            self.remove_invalid_filters(filter, priv_key_string)

    def add_to_invalid_filters(self, filter: "Filter"):
        self.invalid_filters.add(filter)

    def remove_invalid_filters(self, filter: "Filter", priv_key_string: str):
        # We can only remove the filter if it's our own filter
        if Encryption.is_pubkeys_equal(
            filter.owner_pub_key, self._key_ring.signature_key_pair.public_key
        ):
            logger.info(f"Remove invalid filter {filter}")
            self.set_filter_signing_key(priv_key_string)
            signature_as_base64 = self.get_signature(Filter.clone_without_sig(filter))
            filter_with_sig = Filter.clone_with_sig(filter, signature_as_base64)
            result = self._p2p_service.remove_data(filter_with_sig)
            if not result:
                logger.warning(f"Could not remove filter {filter}")
        else:
            logger.info(
                "The invalid filter is not our own, so we cannot remove it from the network"
            )

    def can_remove_dev_filter(self, priv_key_string: str) -> bool:
        if not priv_key_string:
            return False

        developers_filter = self.get_dev_filter()
        if developers_filter is None:
            logger.warning("There is no persisted dev filter to be removed.")
            return False

        if not self.is_valid_dev_privilege_key(priv_key_string):
            logger.warning("Key is invalid.")
            return False

        private_key = self.to_ec_key(priv_key_string)
        pub_key_as_hex = self.get_pub_key_as_hex(private_key)
        if developers_filter.signer_pub_key_as_hex != pub_key_as_hex:
            logger.warning(
                f"pubKeyAsHex derived from private key does not match filterSignerPubKey. "
                f"filterSignerPubKey={developers_filter.signer_pub_key_as_hex}, "
                f"pubKeyAsHex derived from private key={pub_key_as_hex}"
            )
            return False

        if self.is_privileged_dev_pub_key_banned(pub_key_as_hex):
            logger.warning("Pub key is banned.")
            return False

        return True

    def remove_dev_filter(self, priv_key_string: str):
        self.set_filter_signing_key(priv_key_string)
        filter_with_sig = self._user.developers_filter
        if filter_with_sig is None:
            logger.warning(
                "remove_dev_filter: filter_with_sig == None. Should not happen as UI button is deactivated in that case"
            )
            return

        if self._p2p_service.remove_data(filter_with_sig):
            self._user.set_developers_filter(None)
        else:
            logger.warning("Removing dev filter from network failed")

    def add_listener(self, listener: Listener):
        self.listeners.add(listener)

    def get_filter(self) -> Optional[Filter]:
        return self.filter_property.get()

    def get_dev_filter(self) -> Optional[Filter]:
        return self._user.developers_filter

    def get_owner_pub_key(self):
        return self._key_ring.signature_key_pair.public_key

    def is_currency_banned(self, currency_code: str) -> bool:
        filter = self.get_filter()
        return (
            filter is not None
            and filter.banned_currencies is not None
            and any(c == currency_code for c in filter.banned_currencies)
        )

    def is_payment_method_banned(self, payment_method: "PaymentMethod") -> bool:
        filter = self.get_filter()
        return (
            filter is not None
            and filter.banned_payment_methods is not None
            and any(m == payment_method.id for m in filter.banned_payment_methods)
        )

    def is_offer_id_banned(self, offer_id: str) -> bool:
        filter = self.get_filter()
        return filter is not None and any(
            o == offer_id for o in filter.banned_offer_ids
        )

    def is_node_address_banned(self, node_address: "NodeAddress") -> bool:
        filter = self.get_filter()
        return filter is not None and any(
            a == node_address.get_full_address()
            for a in filter.node_addresses_banned_from_trading
        )

    def is_node_address_banned_from_network(self, node_address: "NodeAddress") -> bool:
        filter = self.get_filter()
        return filter is not None and any(
            a == node_address.get_full_address()
            for a in filter.node_addresses_banned_from_network
        )

    def is_auto_conf_explorer_banned(self, address: str) -> bool:
        filter = self.get_filter()
        return filter is not None and any(
            a == address for a in filter.banned_auto_conf_explorers
        )

    def require_update_to_new_version_for_trading(self) -> bool:
        filter = self.get_filter()
        if filter is None:
            return False

        require_update_to_new_version = False
        disable_trade_below_version = filter.disable_trade_below_version
        if disable_trade_below_version and len(disable_trade_below_version) > 0:
            require_update_to_new_version = Version.is_new_version(
                disable_trade_below_version
            )

        return require_update_to_new_version

    def require_update_to_new_version_for_dao(self) -> bool:
        filter = self.get_filter()
        if filter is None:
            return False

        require_update_to_new_version = False
        disable_dao_below_version = filter.disable_dao_below_version
        if disable_dao_below_version and len(disable_dao_below_version) > 0:
            require_update_to_new_version = Version.is_new_version(
                disable_dao_below_version
            )

        return require_update_to_new_version

    def are_peers_payment_account_data_banned(
        self, payment_account_payload: "PaymentAccountPayload"
    ) -> bool:
        filter = self.get_filter()
        if filter is None or payment_account_payload is None:
            return False

        for payment_account_filter in filter.banned_payment_accounts:
            if (
                payment_account_filter.payment_method_id
                != payment_account_payload.payment_method_id
            ):
                continue

            try:
                method = getattr(
                    payment_account_payload, payment_account_filter.get_method_name
                )
                # We invoke getter methods (no args), e.g. getHolderName
                value_from_invoke = method()
                if (
                    isinstance(value_from_invoke, str)
                    and value_from_invoke.lower()
                    == payment_account_filter.value.lower()
                ):
                    return True
            except Exception as e:
                logger.error(
                    f"Error in are_peers_payment_account_data_banned: {str(e)}"
                )
                return False

        return False

    def is_delayed_payout_payment_account(
        self, payment_account_payload: "PaymentAccountPayload"
    ) -> bool:
        if self.get_filter() is None or payment_account_payload is None:
            return False

        for payment_account_filter in self.get_filter().delayed_payout_payment_accounts:
            if (
                payment_account_filter.payment_method_id
                != payment_account_payload.payment_method_id
            ):
                continue

            try:
                method = getattr(
                    payment_account_payload, payment_account_filter.get_method_name
                )
                # We invoke getter methods (no args), e.g. getHolderName
                value_from_invoke = method()
                if (
                    isinstance(value_from_invoke, str)
                    and value_from_invoke.lower()
                    == payment_account_filter.value.lower()
                ):
                    return True
            except Exception as e:
                logger.error(f"Error in is_delayed_payout_payment_account: {str(e)}")
                return False

        return False

    def is_witness_signer_pub_key_banned(
        self, witness_signer_pub_key_as_hex: str
    ) -> bool:
        filter = self.get_filter()
        return (
            filter is not None
            and filter.banned_account_witness_signer_pub_keys is not None
            and any(
                e == witness_signer_pub_key_as_hex
                for e in filter.banned_account_witness_signer_pub_keys
            )
        )

    def is_proof_of_work_valid(self, offer: "Offer") -> bool:
        filter = self.get_filter()
        if filter is None:
            return True

        check_argument(
            offer.bsq_swap_offer_payload is not None,
            "Offer payload must be BsqSwapOfferPayload",
        )
        pow = offer.bsq_swap_offer_payload.get_proof_of_work()
        service = pow_service_for_version(pow.version)
        return (
            service is not None
            and pow.version in self.get_enabled_pow_versions()
            and service.verify_with_ids(
                pow, offer.id, str(offer.owner_node_address), filter.pow_difficulty
            )
        )

    def get_enabled_pow_versions(self) -> list[int]:
        filter = self.get_filter()
        return (
            filter.enabled_pow_versions
            if filter is not None and filter.enabled_pow_versions
            else [0]
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_filter_added_from_network(self, filter_from_network: "Filter"):
        current_filter = self.get_filter()

        if not self.is_filter_public_key_in_list(filter_from_network):
            if filter_from_network.signer_pub_key_as_hex:
                logger.warning(
                    f"isFilterPublicKeyInList failed. Filter.getSignerPubKeyAsHex={filter_from_network.signer_pub_key_as_hex}"
                )
            else:
                logger.info(
                    "isFilterPublicKeyInList failed. Filter.getSignerPubKeyAsHex not set (expected case for pre v1.3.9 filter)"
                )
            return

        if not self.is_signature_valid(filter_from_network):
            logger.warning(f"verifySignature failed. Filter={filter_from_network}")
            return

        if current_filter is not None:
            if current_filter.creation_date > filter_from_network.creation_date:
                logger.info(
                    "We received a new filter from the network but the creation date is older than the "
                    "filter we have already. We ignore the new filter."
                )
                self.add_to_invalid_filters(filter_from_network)
                return

            if self.is_privileged_dev_pub_key_banned(
                filter_from_network.signer_pub_key_as_hex
            ):
                logger.warning(
                    f"Pub key of filter is banned. currentFilter={current_filter}, newFilter={filter_from_network}"
                )
                return
            else:
                logger.info(
                    "We received a new filter with a newer creation date and the signer is not banned. "
                    "We ignore the current (older) filter."
                )
                self.add_to_invalid_filters(current_filter)

        # Our new filter is newer so we apply it.
        # We do not require strict guarantees here (e.g. clocks not synced) as only trusted developers have the key
        # for deploying filters and this is only in place to avoid unintended situations of multiple filters
        # from multiple devs or if same dev publishes new filter from different app without the persisted devFilter.
        self.filter_property.set(filter_from_network)

        # Seed nodes are requested at startup before we get the filter so we only apply the banned
        # nodes at the next startup and don't update the list in the P2P network domain.
        # We persist it to the property file which is read before any other initialisation.
        self.save_banned_nodes(
            FilterManager.BANNED_SEED_NODES, filter_from_network.seed_nodes
        )
        self.save_banned_nodes(
            FilterManager.BANNED_BTC_NODES, filter_from_network.btc_nodes
        )
        self.save_banned_nodes(
            FilterManager.FILTER_PROVIDED_BTC_NODES, filter_from_network.added_btc_nodes
        )
        self.save_banned_nodes(
            FilterManager.FILTER_PROVIDED_SEED_NODES,
            filter_from_network.added_seed_nodes,
        )

        # Banned price relay nodes we can apply at runtime
        price_relay_nodes = filter_from_network.price_relay_nodes
        self.save_banned_nodes(
            FilterManager.BANNED_PRICE_RELAY_NODES, price_relay_nodes
        )

        # TODO should be moved to client with listening on onFilterAdded
        self._price_feed_node_address_provider.apply_banned_nodes(price_relay_nodes)

        # TODO should be moved to client with listening on onFilterAdded
        # NOTE: This part is commented out since it references preferences, which was removed
        # if (new_filter.prevent_public_btc_network and
        #         self.preferences.bitcoin_nodes_option_ordinal == BtcNodes.BitcoinNodesOption.PUBLIC.ordinal()):
        #     self.preferences.set_bitcoin_nodes_option_ordinal(BtcNodes.BitcoinNodesOption.PROVIDED.ordinal())

        for listener in self.listeners:
            listener(filter_from_network)

    def on_filter_removed_from_network(self, filter: Filter):
        if not self.is_filter_public_key_in_list(filter):
            logger.warning(f"isFilterPublicKeyInList failed. Filter={filter}")
            return
        if not self.is_signature_valid(filter):
            logger.warning(f"verifySignature failed. Filter={filter}")
            return

        # We don't check for banned filter as we want to remove a banned filter anyway.

        if (
            self.filter_property.get() is not None
            and self.filter_property.get() != filter
        ):
            return

        self.clear_banned_nodes()

        if filter == self._user.developers_filter:
            self._user.set_developers_filter(None)
        self.filter_property.set(None)

    # Clears options files from banned nodes
    def clear_banned_nodes(self):
        self.save_banned_nodes(FilterManager.BANNED_BTC_NODES, None)
        self.save_banned_nodes(FilterManager.FILTER_PROVIDED_BTC_NODES, None)
        self.save_banned_nodes(FilterManager.BANNED_SEED_NODES, None)
        self.save_banned_nodes(FilterManager.FILTER_PROVIDED_SEED_NODES, None)
        self.save_banned_nodes(FilterManager.BANNED_PRICE_RELAY_NODES, None)

        if self._price_feed_node_address_provider.banned_nodes is not None:
            self._price_feed_node_address_provider.apply_banned_nodes(None)

    def save_banned_nodes(self, option_name: str, banned_nodes: Optional[list[str]]):
        if banned_nodes is not None:
            self._config_file_editor.set_option(option_name, ",".join(banned_nodes))
        else:
            self._config_file_editor.clear_option(option_name)

    def is_valid_dev_privilege_key(self, priv_key_string: str) -> bool:
        try:
            private_key = self.to_ec_key(priv_key_string)
            pub_key = self.get_pub_key_as_hex(private_key)
            return self.is_public_key_in_list(pub_key)
        except Exception as e:
            return False

    def set_filter_signing_key(self, priv_key_string: str):
        self.filter_signing_key = self.to_ec_key(priv_key_string)

    def get_signature(self, filter_without_signature: "Filter"):
        hash_bytes = self.get_filter_sha256_hash(filter_without_signature)
        signature = self.filter_signing_key.ecdsa_sign_recoverable(hash_bytes)
        return base64.b64encode(signature).decode("utf-8")

    def is_filter_public_key_in_list(self, filter: "Filter") -> bool:
        signer_pub_key_as_hex = filter.signer_pub_key_as_hex
        if not self.is_public_key_in_list(signer_pub_key_as_hex):
            logger.info(
                "Invalid filter (expected case for pre v1.3.9 filter as we still keep that in the network "
                + "but the new version does not recognize it as valid filter): "
                + "signerPubKeyAsHex from filter is not part of our pub key list. "
                + f"signerPubKeyAsHex={signer_pub_key_as_hex}, publicKeys={self.public_keys}, filterCreationDate={datetime.fromtimestamp(filter.creation_date/1000)}"
            )
            return False
        return True

    def is_public_key_in_list(self, pub_key_as_hex: str) -> bool:
        is_public_key_in_list = pub_key_as_hex in self.public_keys
        if not is_public_key_in_list:
            logger.info(
                f"pubKeyAsHex is not part of our pub key list (expected case for pre v1.3.9 filter). "
                f"pubKeyAsHex={pub_key_as_hex}, publicKeys={self.public_keys}"
            )
        return is_public_key_in_list

    def is_signature_valid(self, filter: "Filter") -> bool:
        try:
            filter_for_sig_verification = Filter.clone_without_sig(filter)
            hash_bytes = self.get_filter_sha256_hash(filter_for_sig_verification)

            assert (
                filter.signature_as_base64 is not None
            ), "filter.signature_as_base64 must not be None"
            sigdata = base64.b64decode(filter.signature_as_base64)
            pubkey = Encryption.get_ec_public_key_from_bytes(
                bytes.fromhex(filter.signer_pub_key_as_hex)
            )
            return pubkey.ecdsa_verify(sigdata, hash_bytes)
        except Exception as e:
            logger.warning(f"verify_signature failed. filter={filter}")
            return False

    def to_ec_key(self, priv_key_string: str) -> ECPrivkey:
        return Encryption.get_ec_private_key_from_int_hex_string(priv_key_string)

    def get_filter_sha256_hash(self, filter: Filter) -> bytes:
        return get_sha256_hash(filter.serialize_for_hash())

    def get_pub_key_as_hex(self, private_key: ECPrivkey) -> str:
        return private_key.get_public_key_hex()
