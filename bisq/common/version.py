from typing import List, Optional

from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)

class Version:
    # The application versions
    # VERSION = 0.5.0 introduces proto buffer for the P2P network and local DB and is a not backward compatible update
    # Therefore all sub versions start again with 1
    # We use semantic versioning with major, minor and patch
    VERSION = "1.9.18"

    # Holds a list of the tagged resource files for optimizing the getData requests.
    # This must not contain each version but only those where we add new version-tagged resource files for
    # historical data stores.
    HISTORICAL_RESOURCE_FILE_VERSION_TAGS: List[str] = [
        "1.4.0", "1.5.0", "1.5.2", "1.5.5", "1.5.7", "1.6.0",
        "1.6.3", "1.6.5", "1.7.2", "1.7.4", "1.8.0", "1.8.1",
        "1.8.3", "1.9.0", "1.9.3", "1.9.5", "1.9.6", "1.9.7",
        "1.9.10", "1.9.11", "1.9.13", "1.9.15", "1.9.16", "1.9.18"
    ]
    
    @staticmethod
    def get_major_version(version: str) -> int:
        return Version.get_sub_version(version, 0)

    @staticmethod
    def get_minor_version(version: str) -> int:
        return Version.get_sub_version(version, 1)

    @staticmethod
    def get_patch_version(version: str) -> int:
        return Version.get_sub_version(version, 2)

    @staticmethod
    def is_new_version(new_version: str, current_version: str = VERSION) -> bool:
        if new_version == current_version:
            return False
        new_major = Version.get_major_version(new_version)
        current_major = Version.get_major_version(current_version)
        if new_major > current_major:
            return True
        if new_major < current_major:
            return False
        new_minor = Version.get_minor_version(new_version)
        current_minor = Version.get_minor_version(current_version)
        if new_minor > current_minor:
            return True
        if new_minor < current_minor:
            return False
        new_patch = Version.get_patch_version(new_version)
        current_patch = Version.get_patch_version(current_version)
        return new_patch > current_patch

    @staticmethod
    def get_sub_version(version: str, index: int) -> int:
        split = version.split(".")
        if len(split) != 3:
            raise ValueError(f"Version number must be in semantic version format (contain 2 '.'). version={version}")
        return int(split[index])

    # The version no. for the objects sent over the network. A change will break the serialization of old objects.
    # If objects are used for both network and database the network version is applied.
    # VERSION = 0.5.0 -> P2P_NETWORK_VERSION = 1
    # With version 1.2.2 we change to version 2 (new trade protocol)
    P2P_NETWORK_VERSION = 1

    # The version no. of the serialized data stored to disc. A change will break the serialization of old objects.
    # VERSION = 0.5.0 -> LOCAL_DB_VERSION = 1
    LOCAL_DB_VERSION = 1

    # The version no. of the current protocol. The offer holds that version.
    # A taker will check the version of the offers to see if his version is compatible.
    # For the switch to version 2, offers created with the old version will become invalid and have to be canceled.
    # For the switch to version 3, offers created with the old version can be migrated to version 3 just by opening
    # the Bisq app.
    # VERSION = 0.5.0 -> TRADE_PROTOCOL_VERSION = 1
    # Version 1.2.2 -> TRADE_PROTOCOL_VERSION = 2
    # Version 1.5.0 -> TRADE_PROTOCOL_VERSION = 3
    # Version 1.7.0 -> TRADE_PROTOCOL_VERSION = 4
    TRADE_PROTOCOL_VERSION = 4
    p2p_message_version = 0

    BSQ_TX_VERSION = "1"
    
    def get_p2p_message_version() -> int:
        return Version.p2p_message_version

    # The version for the crypto network (BTC_Mainnet = 0, BTC_TestNet = 1, BTC_Regtest = 2, ...)
    BASE_CURRENCY_NETWORK = 0

    def set_base_crypto_network_id(base_crypto_network_id: int):
        Version.BASE_CURRENCY_NETWORK = base_crypto_network_id
        # CRYPTO_NETWORK_ID is ordinal of enum. We use for changes at NETWORK_PROTOCOL_VERSION a multiplication with 10
        # to not mix up networks:
        Version.p2p_message_version = Version.BASE_CURRENCY_NETWORK + 10 * Version.P2P_NETWORK_VERSION

    def get_base_currency_network() -> int:
        return Version.BASE_CURRENCY_NETWORK

    def print_version():
        logger.info(
            f"Version{{"
            f"VERSION={Version.VERSION}, "
            f"P2P_NETWORK_VERSION={Version.P2P_NETWORK_VERSION}, "
            f"LOCAL_DB_VERSION={Version.LOCAL_DB_VERSION}, "
            f"TRADE_PROTOCOL_VERSION={Version.TRADE_PROTOCOL_VERSION}, "
            f"BASE_CURRENCY_NETWORK={Version.BASE_CURRENCY_NETWORK}, "
            f"getP2PNetworkId()={Version.get_p2p_message_version()}"
            f"}}"
        )

    def find_commit_hash() -> Optional[str]:
        raise RuntimeError('Not implemented')

    COMPENSATION_REQUEST = b'\x01'
    REIMBURSEMENT_REQUEST = b'\x01'
    PROPOSAL = b'\x01'
    BLIND_VOTE = b'\x01'
    VOTE_REVEAL = b'\x01'
    LOCKUP = b'\x01'
    ASSET_LISTING_FEE = b'\x01'
    PROOF_OF_BURN = b'\x01'