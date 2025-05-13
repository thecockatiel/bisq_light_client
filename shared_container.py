from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.core.user.preferences import Preferences
    from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
    from bisq.common.setup.uncought_exception_handler import UncaughtExceptionHandler
    from bisq.common.persistence.persistence_orchestrator import PersistenceOrchestrator
    from bisq.common.file.corrupted_storage_file_handler import (
        CorruptedStorageFileHandler,
    )
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
    from bisq.core.api.core_context import CoreContext
    from utils.clock import Clock
    from bisq.common.config.config import Config
    from bisq.core.user.user_manager import UserManager


class SharedContainer:
    def __init__(
        self,
        core_context: "CoreContext",
        config: "Config",
        persistence_orchestrator: "PersistenceOrchestrator",
        uncought_exception_handler: "UncaughtExceptionHandler",
        graceful_shutdown_handler: "GracefulShutDownHandler",
        user_manager: "UserManager",
        clock: "Clock",
        network_proto_resolver: "NetworkProtoResolver",
        corrupted_storage_file_handler: "CorruptedStorageFileHandler",
        preferences: "Preferences",
    ):
        self.core_context = core_context
        self._config = config
        self._user_manager = user_manager
        self.uncought_exception_handler = uncought_exception_handler
        self.graceful_shutdown_handler = graceful_shutdown_handler
        self.persistence_orchestrator = persistence_orchestrator
        self.clock = clock
        self.network_proto_resolver = network_proto_resolver
        self.corrupted_storage_file_handler = corrupted_storage_file_handler
        self.preferences = preferences

    def __getattr__(self, name):
        return None

    @property
    def config(self):
        if self._config is None:
            from bisq.common.config.config import Config
            from utils.dir import user_data_dir

            self._config = Config("bisq_light", user_data_dir())

        return self._config

    @property
    def clock_watcher(self):
        if self._clock_watcher is None:
            from bisq.common.clock_watcher import ClockWatcher

            self._clock_watcher = ClockWatcher()

        return self._clock_watcher

    @property
    def btc_formatter(self):
        if self._btc_formatter is None:
            from bisq.core.util.coin.immutable_coin_formatter import (
                ImmutableCoinFormatter,
            )

            self._btc_formatter = ImmutableCoinFormatter(
                self.config.base_currency_network_parameters.get_monetary_format()
            )
        return self._btc_formatter

    @property
    def bsq_formatter(self):
        if self._bsq_formatter is None:
            from bisq.core.util.coin.bsq_formatter import BsqFormatter

            self._bsq_formatter = BsqFormatter(self.config)
        return self._bsq_formatter
