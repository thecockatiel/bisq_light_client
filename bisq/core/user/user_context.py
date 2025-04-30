import logging
from threading import Lock
from bisq.common.ascii_logo import show_ascii_logo
from bisq.common.persistence.persistence_orchestrator import PersistenceOrchestrator
from bisq.common.util.utilities import get_sys_info
from bisq.common.version import Version
from bisq.core.setup.core_network_capabilities import CoreNetworkCapabilities
from shared_container import SharedContainer
from utils.aio import as_future
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional
from bisq.core.app.bisq_headless_app import BisqHeadlessApp
from bisq.common.setup.log_setup import (
    get_user_log_file_path,
    logger_context,
    remove_user_handler_from_shared,
    switch_std_handler_to,
    add_user_handler_to_shared,
)
from bisq.core.setup.core_persisted_data_host import CorePersistedDataHost
from bisq.core.user.preferences import Preferences
from bisq.core.user.user import User
from global_container import GlobalContainer
from utils.concurrency import AtomicInt
from twisted.internet.defer import Deferred
import asyncio


@dataclass
class UserContext:
    user_id: str
    alias: str
    user: User
    preferences: Preferences
    persistence_orchestrator: PersistenceOrchestrator
    logger: logging.Logger
    global_container: Optional[GlobalContainer] = field(default=None)
    _lock: Lock = field(default_factory=lambda: Lock(), init=False)
    """only not None when UserManager.init_user has been called for user_id"""

    @property
    def key_ring(self):
        return self.user.key_ring

    def __eq__(self, other):
        if not isinstance(other, UserContext):
            return False
        return self.user_id == other.user_id

    def __repr__(self):
        return f"User(id={self.user_id}, alias={self.alias})"

    async def _read_all_persisted_user_data(
        self,
    ):
        # TODO: make reading async at persistence manager
        hosts = CorePersistedDataHost.get_persisted_data_hosts(self.global_container)

        remaining = AtomicInt(len(hosts))
        d = Deferred()

        def _on_host_read():
            if remaining.decrement_and_get() == 0:
                d.callback(True)

        for host in hosts:
            host.read_persisted(_on_host_read)

        await as_future(d)

    async def start(
        self, shared_container: "SharedContainer", should_take_std_out=False
    ):
        with self._lock:
            try:
                add_user_handler_to_shared(self.user_id)
                if should_take_std_out:
                    switch_std_handler_to(self.user_id)
                self.logger.info(
                    f"User log file at: {get_user_log_file_path(self.user.data_dir)}"
                )
                with logger_context(self.logger):
                    self.logger.info(get_sys_info())
                    show_ascii_logo()
                    Version.print_version()
                    CoreNetworkCapabilities.print_capabilities()
                    self.global_container = GlobalContainer(
                        shared_container,
                        self.user,
                        self.preferences,
                        self.persistence_orchestrator,
                    )
                    self.preferences.fee_service = self.global_container.fee_service
                    await self._read_all_persisted_user_data()
                    if shared_container.config.gui_mode:
                        # TODO gui app
                        raise NotImplementedError("Gui mode not implemented yet")
                    else:
                        BisqHeadlessApp(
                            shared_container.uncought_exception_handler,
                            shared_container.graceful_shutdown_handler,
                            self,
                        ).start_user_instance()
            except BaseException as e:
                self.logger.error("Error while starting user context", exc_info=e)
                raise e

    async def shut_down(self) -> asyncio.Future[int]:
        d = Deferred()
        try:
            with self._lock:
                if self.global_container:
                    with logger_context(self.logger):
                        self.global_container.open_bsq_swap_offer_service.shut_down()
                        self.global_container.price_feed_service.shut_down()
                        self.global_container.arbitrator_manager.shut_down()
                        self.global_container.trade_statistics_manager.shut_down()
                        self.global_container.xmr_tx_proof_service.shut_down()
                        self.global_container.dao_setup.shut_down()
                        self.logger.info("OpenOfferManager shutdown started")

                        def shut_down_finished(ecode: int):
                            self.global_container = None
                            self.logger = None
                            remove_user_handler_from_shared(self.user_id)
                            d.callback(ecode)

                        self.global_container.open_offer_manager.shut_down(
                            lambda: self._on_open_offer_manager_shutdown(shut_down_finished)
                        )
                else:
                    d.callback(0)
        except BaseException as e:
            d.errback(e)
        return await as_future(d)

    def _on_open_offer_manager_shutdown(self, result_handler: Callable[[int], None]):
        self.logger.info("OpenOfferManager shutdown completed")
        self.global_container.btc_wallet_service.shut_down()
        self.global_container.bsq_wallet_service.shut_down()

        wallets_setup = self.global_container.wallets_setup
        wallets_setup.shut_down_complete_property.add_listener(
            lambda _: self._on_wallets_setup_shutdown(result_handler)
        )
        wallets_setup.shut_down()

    def _on_wallets_setup_shutdown(self, result_handler: Callable[[], None]):
        self.logger.info("WalletsSetup shutdown completed")
        self.global_container.p2p_service.shut_down(
            lambda: self._on_p2p_service_shutdown(result_handler)
        )

    def _on_p2p_service_shutdown(self, result_handler: Callable[[], None]):
        self.logger.info("P2PService shutdown completed")
        self.logger.info("PersistenceManager flushAllDataToDiskAtShutdown started")
        self.global_container.persistence_orchestrator.flush_all_data_to_disk_at_shutdown(
            lambda: self._on_flush_complete(result_handler)
        )

    def _on_flush_complete(self, result_handler: Callable[[], None]):
        self.logger.info("Graceful shutdown completed. Exiting now.")
        result_handler(0)

    def __hash__(self):
        return hash(self.user_id)
