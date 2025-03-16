from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import timedelta
import sys
from typing import TYPE_CHECKING, Optional

from utils.aio import stop_reactor_and_exit
from bisq.common.config.config_exception import ConfigException
from bisq.common.persistence.persistence_manager import PersistenceManager
from bisq.common.setup.common_setup import CommonSetup
from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.common.user_thread import UserThread
from bisq.core.app.bisq_setup_listener import BisqSetupListener
from bisq.core.setup.core_persisted_data_host import CorePersistedDataHost
from bisq.core.setup.core_setup import CoreSetup
from global_container import GlobalContainer, set_global_container
from utils.concurrency import AtomicBoolean, AtomicInt
from utils.dir import user_data_dir
from threading import Timer, Thread
from bisq.common.setup.log_setup import configure_logging, get_logger
from bisq.common.config.config import Config

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
import traceback

logger = get_logger(__name__)

class BisqExecutable(
    GracefulShutDownHandler, BisqSetupListener, UncaughtExceptionHandler, ABC
):
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1

    def __init__(
        self,
        full_name: str,
        script_name: str,
        app_name: str,
        version: str,
    ):
        self.full_name = full_name
        self.script_name = script_name
        self.app_name = app_name
        self.version = version
        
        self.__is_shutdown_in_progress = AtomicBoolean(False)
        self._has_downgraded = False
        self._injector: Optional["GlobalContainer"] = None
        self._config: Optional["Config"] = None
        
    def execute(self):
        try:
            self._config = Config(self.app_name, user_data_dir())
            if self._config.help_requested:
                self._config.parser.print_help()
                return stop_reactor_and_exit(BisqExecutable.EXIT_SUCCESS)
            configure_logging(log_file=self._config.app_data_dir.joinpath("bisq.log"), log_level=self._config.log_level)
            if self._config.full_dao_node:
                logger.error("Full DAO node is not supported. ignoring this option.")
                self._config.full_dao_node = False
                self._config.full_dao_node_option_set_explicitly = False
        except ConfigException as e:
            print(f"error: {e}", file=sys.stderr)
            return stop_reactor_and_exit(BisqExecutable.EXIT_FAILURE)
        except Exception as e:
            print(f"fault: An unexpected error occurred. Please file a report at https://github.com/thecockatiel/bisq_light_client", file=sys.stderr)
            traceback.print_exc()
            return stop_reactor_and_exit(BisqExecutable.EXIT_FAILURE)
        
        self.do_execute()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // First synchronous execution tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def do_execute(self):
        CommonSetup.setup(self._config, self)
        CoreSetup.setup(self._config)
        
        self.add_capabilities()
        
        self.launch_application()
    
    @abstractmethod
    def config_user_thread(self):
        pass
    
    def add_capabilities(self):
        pass
    
    @abstractmethod
    def launch_application(self):
        pass
    
    def on_application_launched(self):
        self.config_user_thread()
        
        # Now we can use the user thread start periodic tasks
        CommonSetup.start_periodic_tasks()
        
        # As the handler method might be overwritten by subclasses and they use the application as handler
        # we need to setup the handler after the application is created.
        CommonSetup.setup_uncaught_exception_handler(self)
        self.setup_injector()
        
        self._has_downgraded = self._injector.bisq_setup.has_downgraded()
        if self._has_downgraded:
            # If user tried to downgrade we do not read the persisted data to avoid data corruption
            # We call startApplication to enable UI to show popup. We prevent in BisqSetup to go further
            # in the process and require a shut down.
            self.start_application()
        else:
            self.read_all_persisted(self.start_application)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // We continue with a series of synchronous execution tasks
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    @abstractmethod
    def init_core_module(self):
        pass
    
    def setup_injector(self):
        self.init_core_module()
        self._injector = GlobalContainer()
        self._injector._config = self._config
        set_global_container(self._injector)
        self.apply_injector()

    def apply_injector(self):
        # Subclasses might configure classes with the injector here
        pass
    
    def read_all_persisted(self, complete_handler: Callable[[], None], additional_hosts: Optional[list["PersistedDataHost"]] = None):
        hosts = CorePersistedDataHost.get_persisted_data_hosts(self._injector)
        if additional_hosts:
            hosts.extend(additional_hosts)
            
        remaining = AtomicInt(len(hosts))
        
        def _on_host_read():
            if remaining.decrement_and_get() == 0:
                UserThread.execute(complete_handler)

        for host in hosts:
            host.read_persisted(_on_host_read)
        
    def setup_avoid_standby_mode(self):
        pass
    
    @abstractmethod
    def start_application(self):
        pass
    
    def on_application_started(self):
        self.run_bisq_setup()
        self.setup_avoid_standby_mode()

    def run_bisq_setup(self):
        bisq_setup = self._injector.bisq_setup
        bisq_setup.add_bisq_setup_listener(self)
        bisq_setup.start()
    
    @abstractmethod
    def on_setup_complete(self):
        pass
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // GracefulShutDownHandler implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # This might need to be overwritten in case the application is not using all modules
    def graceful_shut_down(self, result_handler: Callable[[int], None]):
        if self.__is_shutdown_in_progress.get_and_set(True):
            return
        logger.info("Start graceful shutDown")

        if self._injector is None:
            logger.info("Shut down called before injector was created")
            result_handler(BisqExecutable.EXIT_SUCCESS)

        def timeout_handler():
            logger.warning("Graceful shutdown not completed in 10 sec. Triggering timeout handler.")
            # We create another thread because:
            # - UserThread can be blocked by a shutdown routine
            # - Timer thread is daemon so it can die in middle of flush_and_exit
            Thread(target=self.flush_and_exit, name="flush_and_exit", args=(result_handler, BisqExecutable.EXIT_SUCCESS)).start()

        # We do not use the UserThread to avoid that the timeout would not get triggered in case the UserThread
        # would get blocked by a shutdown routine.
        timer = Timer(10.0, timeout_handler)
        timer.daemon = True
        timer.start()

        try:
            self._injector.clock_watcher.shut_down()
            self._injector.open_bsq_swap_offer_service.shut_down()
            self._injector.price_feed_service.shut_down()
            self._injector.arbitrator_manager.shut_down()
            self._injector.trade_statistics_manager.shut_down()
            self._injector.xmr_tx_proof_service.shut_down()
            # self._injector.rpc_service.shut_down() # TODO
            self._injector.dao_setup.shut_down()
            # self._injector.avoid_standby_mode_service.shut_down() # TODO
            logger.info("OpenOfferManager shutdown started")
            self._injector.open_offer_manager.shut_down(lambda: self._on_open_offer_manager_shutdown(result_handler))
        except Exception as e:
            logger.error("App shutdown failed with an exception", exc_info=e)
            self.flush_and_exit(result_handler, BisqExecutable.EXIT_FAILURE)

    def _on_open_offer_manager_shutdown(self, result_handler: Callable[[], None]):
        logger.info("OpenOfferManager shutdown completed")
        self._injector.btc_wallet_service.shut_down()
        self._injector.bsq_wallet_service.shut_down()

        wallets_setup = self._injector.wallets_setup
        wallets_setup.shut_down_complete_property.add_listener(lambda _: self._on_wallets_setup_shutdown(result_handler))
        wallets_setup.shut_down()

    def _on_wallets_setup_shutdown(self, result_handler: Callable[[], None]):
        logger.info("WalletsSetup shutdown completed")
        self._injector.p2p_service.shut_down(lambda: self._on_p2p_service_shutdown(result_handler))

    def _on_p2p_service_shutdown(self, result_handler: Callable[[], None]):
        logger.info("P2PService shutdown completed")
        self.flush_and_exit(result_handler, BisqExecutable.EXIT_SUCCESS)

    def flush_and_exit(self, result_handler: Callable[[], None], status: int):
        if not self._has_downgraded:
            # If user tried to downgrade we do not write the persistable data to avoid data corruption
            logger.info("PersistenceManager flushAllDataToDiskAtShutdown started")
            PersistenceManager.flush_all_data_to_disk_at_shutdown(lambda: self._on_flush_complete(result_handler, status))
        else:
            self._on_flush_complete(result_handler, status)

    def _on_flush_complete(self, result_handler: Callable[[], None], status: int):
        logger.info("Graceful shutdown completed. Exiting now.")
        result_handler(status)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // UncaughtExceptionHandler implementation
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_uncaught_exception(self, exception: Exception, do_shut_down: bool):
        logger.error(f"Uncaught exception: {exception}", exc_info=exception)

        if do_shut_down:
            self.graceful_shut_down(lambda *_: logger.info("graceful_shut_down complete"))
