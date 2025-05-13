import contextvars
from bisq.core.api.core_context import CoreContext
from bisq.core.protocol.persistable.core_persistence_proto_resolver import (
    CorePersistenceProtoResolver,
)
from bisq.daemon.grpc.grpc_container import GrpcContainer
from utils.aio import as_future, stop_reactor_and_exit
from collections.abc import Callable
import sys
from threading import Thread, Timer
import traceback
from bisq.common.config.config import Config
from bisq.common.config.config_exception import ConfigException
from bisq.common.file.corrupted_storage_file_handler import CorruptedStorageFileHandler
from bisq.common.setup.common_setup import CommonSetup
from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
from bisq.common.setup.log_setup import (
    get_base_logger,
    get_base_logger,
    setup_aggregated_logger,
    logger_context,
)
from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
from bisq.common.version import Version
from bisq.core.setup.core_setup import CoreSetup
from shared_container import SharedContainer
import asyncio
from typing import TYPE_CHECKING, Optional
from twisted.internet.defer import Deferred

from utils.clock import Clock
from utils.concurrency import AtomicBoolean, AtomicInt
from utils.dir import user_data_dir
from bisq.common.persistence.persistence_orchestrator import PersistenceOrchestrator

if TYPE_CHECKING:
    from bisq.common.protocol.persistable.persistence_proto_resolver import (
        PersistenceProtoResolver,
    )
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.user.user_manager import UserManager
    from bisq.shared.preferences.preferences import Preferences

base_logger = get_base_logger(__name__)
shared_logger = get_base_logger(__name__)


class BisqDaemonMain(
    GracefulShutDownHandler,
    UncaughtExceptionHandler,
):
    EXIT_SUCCESS = 0
    EXIT_FAILURE = 1

    def __init__(self):
        self.full_name = "Bisq Light Daemon"
        self.script_name = "bisqd"
        self.app_name = "bisq_light"
        self.version = Version.VERSION

        self.__is_shutdown_in_progress = AtomicBoolean(False)
        self._has_downgraded = False
        self._user_manager: Optional["UserManager"] = None
        self._preferences: Optional["Preferences"] = None
        self._config: Optional["Config"] = None
        self._shared_container: Optional["SharedContainer"] = None
        self._core_context = (
            CoreContext()
        )  # TODO, set is_api_user based on being gui or not
        self._grpc_container: Optional["GrpcContainer"] = None

    async def main(self):
        # entry point
        try:
            self._config = Config(self.app_name, user_data_dir())
            setup_aggregated_logger(self._config.app_data_dir, self._config.log_level)

            if self._config.help_requested:
                self._config.parser.print_help()
                return stop_reactor_and_exit(BisqDaemonMain.EXIT_SUCCESS)

            CoreSetup.setup(self._config)

            # this, and UserManager, needs to be imported after config has initialized,
            # because otherwise `Params` will be initialized with wrong network
            from bisq.core.protocol.network.core_network_proto_resolver import (
                CoreNetworkProtoResolver,
            )

            clock = Clock()
            with logger_context(base_logger):
                corrupted_storage_file_handler = CorruptedStorageFileHandler()
                network_proto_resolver = CoreNetworkProtoResolver(clock)
                shared_persistence_orchestrator = PersistenceOrchestrator()
                persistence_proto_resolver = CorePersistenceProtoResolver(
                    Clock(), None, network_proto_resolver
                )

                await self._init_user_manager(
                    persistence_proto_resolver,
                    corrupted_storage_file_handler,
                    shared_persistence_orchestrator,
                )

                await self._init_preferences(
                    self._user_manager,
                    persistence_proto_resolver,
                    corrupted_storage_file_handler,
                    shared_persistence_orchestrator,
                )

                shared_persistence_orchestrator.on_all_services_initialized()

                self._shared_container = SharedContainer(
                    self._core_context,
                    self._config,
                    shared_persistence_orchestrator,
                    self,
                    self,
                    self._user_manager,
                    clock,
                    network_proto_resolver,
                    corrupted_storage_file_handler,
                    self._preferences,
                )
            if self._config.full_dao_node:
                print("Full DAO node is not supported.")
                return stop_reactor_and_exit(BisqDaemonMain.EXIT_FAILURE)
        except ConfigException as e:
            print(f"error: {e}", file=sys.stderr)
            return stop_reactor_and_exit(BisqDaemonMain.EXIT_FAILURE)
        except Exception as e:
            print(
                f"fault: An unexpected error occurred. Please file a report at https://github.com/thecockatiel/bisq_light_client",
                file=sys.stderr,
            )
            traceback.print_exc()
            return stop_reactor_and_exit(BisqDaemonMain.EXIT_FAILURE)
        else:
            # setup handlers
            with logger_context(base_logger):
                CommonSetup.setup_sig_int_handlers(self)
                CommonSetup.setup(self._config, self)
                CommonSetup.start_periodic_tasks()
                CommonSetup.setup_uncaught_exception_handler(self)

                self._grpc_container = GrpcContainer(
                    self._core_context,
                    self._config,
                    self._user_manager,
                    self._shared_container,
                    self,
                )
                self._grpc_container.grpc_server.start()

            downgrade_handler = None

            if self._config.gui_mode:
                # TODO: setup gui here before continuing (blockingly wait for grpc to have a gui connection in gui mode)
                downgrade_handler = lambda *_: None  # TODO

            self._has_downgraded = CommonSetup.has_downgraded(
                self._config, downgrade_handler
            )
            # If user tried to downgrade we do not read the persisted data to avoid data corruption
            # We tell UI to show popup, if in gui mode, we exit otherwise.
            if self._has_downgraded and not self._config.gui_mode:
                base_logger.error(
                    "User tried to launch with an older version. Exiting to prevent data corruption..."
                )
                return stop_reactor_and_exit(BisqDaemonMain.EXIT_FAILURE)
            elif not self._has_downgraded:
                CommonSetup.persist_bisq_version(self._config)
                self.setup_avoid_standby_mode()
                # TODO: create a function that does the following:
                #   init the active user id in user_manager and call headlessapp.start_user_instance for it
                try:
                    self._user_manager.get_user_context(
                        self._user_manager.active_user_id
                    )
                    active_user_id_unavailable = False
                except:
                    base_logger.warning(
                        f"incosistent state detected, replacing active user (`{self._user_manager.active_user_id}`) with an available one"
                    )
                    active_user_id_unavailable = True
                await self._user_manager.switch_user(
                    (
                        None
                        if active_user_id_unavailable
                        else self._user_manager.active_user_id
                    ),
                    self._shared_container,
                )

            await BisqDaemonMain.keep_running()

    # /////////////////////////////////////////////////////////////////////////////////////
    # // First synchronous execution tasks
    # /////////////////////////////////////////////////////////////////////////////////////

    async def _init_user_manager(
        self,
        persistence_proto_resolver: "PersistenceProtoResolver",
        corrupted_storage_file_handler: "CorruptedStorageFileHandler",
        shared_persistence_orchestrator: "PersistenceOrchestrator",
    ):
        # See comment for CoreNetworkProtoResolver import above
        from bisq.core.user.user_manager import UserManager

        self._user_manager = UserManager(
            self._config,
            persistence_proto_resolver,
            corrupted_storage_file_handler,
            shared_persistence_orchestrator,
        )
        d = Deferred()
        try:
            self._user_manager.read_persisted(lambda: d.callback(True))
        except BaseException as e:
            d.errback(e)
        await as_future(d)

    async def _init_preferences(
        self,
        user_manager: "UserManager",
        persistence_proto_resolver: "PersistenceProtoResolver",
        corrupted_storage_file_handler: "CorruptedStorageFileHandler",
        shared_persistence_orchestrator: "PersistenceOrchestrator",
    ):
        # See comment for CoreNetworkProtoResolver import above
        from bisq.shared.preferences.preferences import Preferences
        from bisq.common.persistence.persistence_manager import PersistenceManager

        self._preferences = Preferences(
            PersistenceManager(
                user_manager.data_dir,
                persistence_proto_resolver,
                corrupted_storage_file_handler,
                shared_persistence_orchestrator,
            ),
            self._config,
        )
        d = Deferred()
        try:
            self._preferences.read_persisted(lambda: d.callback(True))
        except BaseException as e:
            d.errback(e)
        await as_future(d)

    def handle_uncaught_exception(self, exception: Exception, do_shut_down: bool):
        base_logger.error(f"Uncaught exception: {exception}", exc_info=exception)
        if do_shut_down:
            self.graceful_shut_down(
                lambda ecode: shared_logger.info(
                    f"graceful_shut_down complete with code {ecode}"
                )
            )

    def setup_avoid_standby_mode(self):
        # TODO: setup in gui mode
        # we setup avoid standby mode on server because it's where it matters
        pass

    def graceful_shut_down(self, result_handler: "Callable[[int], None]" = None):
        def on_finished_shutdown(status: int):
            shared_logger.info("Graceful shutdown completed. Exiting now.")
            BisqDaemonMain.stop_keep_running()
            if self._grpc_container:
                self._grpc_container.grpc_server.shut_down()
            # result_handler passed by keyboard interrupt or grpc stop command
            if result_handler:
                result_handler(status)
            stop_reactor_and_exit(status)

        self._graceful_shut_down(on_finished_shutdown)

    def _graceful_shut_down(self, result_handler: Callable[[int], None]):
        if self.__is_shutdown_in_progress.get_and_set(True):
            return
        shared_logger.info("Start graceful shutDown")

        if self._user_manager is None:
            shared_logger.info("Shut down called before user_manager was created")
            result_handler(BisqDaemonMain.EXIT_SUCCESS)

        flushing = AtomicBoolean(False)

        def flush_and_exit(status: int):
            if flushing.get_and_set(True):
                # we are already doing that
                return
            remaining_flushes = AtomicInt(1)

            def finished():
                if remaining_flushes.decrement_and_get() == 0:
                    result_handler(status)

            for ctx in self._user_manager.get_all_contexts():
                if (
                    ctx.global_container
                    and ctx.global_container.persistence_orchestrator
                ):
                    remaining_flushes.increment_and_get()
                    ctx.global_container.persistence_orchestrator.flush_all_data_to_disk_at_shutdown(
                        finished
                    )
            self._shared_container.persistence_orchestrator.flush_all_data_to_disk_at_shutdown(
                finished
            )

        def timeout_handler():
            shared_logger.warning(
                "Graceful shutdown not completed in 10 sec. Triggering timeout handler."
            )
            # We create another thread because:
            # - UserThread can be blocked by a shutdown routine
            # - Timer thread is daemon so it can die in middle of flush_and_exit
            ctx = contextvars.copy_context()
            Thread(
                target=ctx.run,
                args=(
                    flush_and_exit,
                    BisqDaemonMain.EXIT_SUCCESS,
                ),
                name="flush_and_exit",
            ).start()

        # We do not use the UserThread to avoid that the timeout would not get triggered in case the UserThread
        # would get blocked by a shutdown routine.
        timer = Timer(10.0, timeout_handler)
        timer.daemon = True
        timer.start()

        try:
            self._shared_container.clock_watcher.shut_down()
            # self._shared_container.avoid_standby_mode_service.shut_down() # TODO
            self._user_manager.shut_down_all_users(flush_and_exit)
        except Exception as e:
            base_logger.error("App shutdown failed with an exception", exc_info=e)
            flush_and_exit(BisqDaemonMain.EXIT_FAILURE)

    _keep_running_future: "asyncio.Future" = None

    @staticmethod
    async def keep_running():
        BisqDaemonMain._keep_running_future = as_future(Deferred())
        await BisqDaemonMain._keep_running_future

    @staticmethod
    def stop_keep_running():
        if BisqDaemonMain._keep_running_future:
            BisqDaemonMain._keep_running_future.cancel()
            BisqDaemonMain._keep_running_future = None
