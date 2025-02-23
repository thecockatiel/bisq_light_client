from abc import ABC, abstractmethod
from collections.abc import Callable, Collection
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.common.crypto.encryption import ECPrivkey, Encryption
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from utils.time import get_time_ms


if TYPE_CHECKING:
    from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
        AccountingBlock,
    )
    from bisq.core.dao.burningman.accounting.node.full.accounting_block_parser import (
        AccountingBlockParser,
    )
    from bisq.core.dao.burningman.burning_man_accounting_service import (
        BurningManAccountingService,
    )
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.user.preferences import Preferences
    from bisq.core.network.p2p.p2p_service import P2PService

logger = get_logger(__name__)


class AccountingNode(DaoSetupService, DaoStateListener, ABC):
    PERMITTED_PUB_KEYS = {
        "02640325af0cc68462664cfacdb4b59754156f293c04aae32b5c8b1650f914fe61", # @jester4042
        "027056a287f80591bde6fff24451c99b2e518bd40a8a04d079aba477e1180f603d" # @runbtc
    }

    def __init__(
        self,
        p2p_service: "P2PService",
        dao_state_service: "DaoStateService",
        burning_man_accounting_service: "BurningManAccountingService",
        accounting_block_parser: "AccountingBlockParser",
        preferences: "Preferences",
    ):
        self._p2p_service = p2p_service
        self._dao_state_service = dao_state_service
        self._burning_man_accounting_service = burning_man_accounting_service
        self._accounting_block_parser = accounting_block_parser
        self._preferences = preferences

        self.error_message_handler: Optional[Callable[[str], None]] = None
        self.warn_message_handler: Optional[Callable[[str], None]] = None
        self._bootstrap_listener: Optional[BootstrapListener] = None
        self._try_reorg_counter = 0
        self._p2p_network_ready = False
        self._initial_block_requests_complete = False

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_chain_complete(self):
        self.on_initial_dao_block_parsing_complete()

        # We get called on_parse_block_chain_complete at each new block arriving but we want to react only after initial
        # parsing is done, so we remove after getting called ourself as listener.
        self._dao_state_service.remove_dao_state_listener(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        if not self._preferences.is_process_burning_man_accounting_data():
            return

        if self._dao_state_service.parse_block_chain_complete:
            logger.info(
                "daoStateService.isParseBlockChainComplete is already true, "
                "we call on_initial_dao_block_parsing_complete directly"
            )
            self.on_initial_dao_block_parsing_complete()
        else:
            self._dao_state_service.add_dao_state_listener(self)

        class Listener(BootstrapListener):
            def on_no_seed_node_available(self_):
                self.on_p2p_network_ready()

            def on_data_received(self_):
                self.on_p2p_network_ready()

        self._bootstrap_listener = Listener()

    def start(self):
        # We do not start yet but wait until DAO block parsing is complete to not interfere with
        # that higher priority activity.
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def shut_down(self):
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def on_initial_dao_block_parsing_complete(self):
        pass

    def on_initialized(self):
        if self._p2p_service.is_bootstrapped():
            logger.info(
                "p2PService.isBootstrapped is already true, we call on_p2p_network_ready directly."
            )
            self.on_p2p_network_ready()
        else:
            self._p2p_service.add_p2p_service_listener(self._bootstrap_listener)

    def on_p2p_network_ready(self):
        self._p2p_network_ready = True
        self._p2p_service.remove_p2p_service_listener(self._bootstrap_listener)

    @abstractmethod
    def start_request_blocks(self):
        pass

    def on_initial_block_requests_complete(self):
        self._initial_block_requests_complete = True
        self._burning_man_accounting_service.on_initial_block_requests_complete()

    def apply_reorg(self):
        logger.warning("apply_reorg called")
        self._try_reorg_counter += 1
        if self._try_reorg_counter < 5:
            self._burning_man_accounting_service.purge_last_ten_blocks()
            # Increase delay at each retry
            delay = self._try_reorg_counter * self._try_reorg_counter
            UserThread.run_after(self.start_request_blocks, timedelta(seconds=delay))
        else:
            logger.warning(
                f"We tried {self._try_reorg_counter} times to request blocks again after a reorg signal but it is still failing.",
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Oracle verification
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def get_sha256_hash(block: "AccountingBlock") -> bytes:
        return get_sha256_hash(block.serialize_for_hash())

    @staticmethod
    def get_sha256_hash_for_collection(
        blocks: Collection["AccountingBlock"],
    ) -> Optional[bytes]:
        ts = get_time_ms()
        try:
            output_stream = bytearray()
            for accounting_block in blocks:
                output_stream.extend(accounting_block.serialize_for_hash())
            hash_value = get_sha256_hash(output_stream)
            logger.info(
                f"get_sha256_hash_for_collection for {len(blocks)} blocks took {get_time_ms() - ts} ms",
            )
            return hash_value
        except Exception as e:
            logger.error(
                "Error while calculating SHA256 hash for collection of blocks",
                exc_info=e,
            )
            return None

    @staticmethod
    def get_signature(sha256hash: bytes, priv_key: ECPrivkey) -> bytes:
        # TODO: check if works same as java
        return priv_key.sign(sha256hash)

    @staticmethod
    def is_valid_pub_key_and_signature(
        sha256_hash: bytes, pub_key: str, signature: bytes, use_dev_privilege_keys: bool
    ) -> bool:
        # TODO: check if works same as java
        if pub_key not in AccountingNode.get_permitted_pub_keys(use_dev_privilege_keys):
            logger.warning(f"PubKey is not in supported key set. pubKey={pub_key}")
            return False

        try:
            ec_pub_key = Encryption.get_ec_public_key_from_bytes(bytes.fromhex(pub_key))
            return ec_pub_key.verify_message_hash(signature, sha256_hash)
        except Exception as e:
            logger.warning("Signature verification failed.")
            return False

    @staticmethod
    def is_permitted_pub_key(use_dev_privilege_keys: bool, pub_key: str) -> bool:
        return pub_key in AccountingNode.get_permitted_pub_keys(use_dev_privilege_keys)

    @staticmethod
    def get_permitted_pub_keys(use_dev_privilege_keys: bool) -> set[str]:
        if use_dev_privilege_keys:
            return {DevEnv.DEV_PRIVILEGE_PUB_KEY}
        return AccountingNode.PERMITTED_PUB_KEYS
