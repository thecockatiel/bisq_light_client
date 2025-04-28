from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bisq.common.setup.graceful_shut_down_handler import GracefulShutDownHandler
    from bisq.core.api.core_context import CoreContext
    from bisq.common.config.config import Config
    from bisq.core.user.user_manager import UserManager
    from shared_container import SharedContainer


class GrpcContainer:
    def __init__(
        self,
        core_context: "CoreContext",
        config: "Config",
        user_manager: "UserManager",
        shared_container: "SharedContainer",
        graceful_shut_down_handler: "GracefulShutDownHandler",
    ):
        self._config = config
        self._user_manager = user_manager
        self._core_context = core_context
        self._shared_container = shared_container
        self._graceful_shut_down_handler = graceful_shut_down_handler

    def __getattr__(self, name):
        return None

    @property
    def core_api(self):
        if self._core_api is None:
            from bisq.core.api.core_api import CoreApi

            self._core_api = CoreApi(
                self._config,
                self._user_manager,
                self._shared_container,
                self.core_dispute_agents_service,
                self.core_help_service,
                self.core_offers_service,
                self.core_payment_accounts_service,
                self.core_price_service,
                self.core_trades_service,
                self.core_wallets_service,
            )
        return self._core_api

    @property
    def core_dispute_agents_service(self):
        if self._core_dispute_agents_service is None:
            from bisq.core.api.core_dipsute_agents_service import (
                CoreDisputeAgentsService,
            )

            self._core_dispute_agents_service = CoreDisputeAgentsService(
                self._config,
            )
        return self._core_dispute_agents_service

    @property
    def core_help_service(self):
        if self._core_help_service is None:
            from bisq.core.api.core_help_service import CoreHelpService

            self._core_help_service = CoreHelpService(self._user_manager)
        return self._core_help_service

    @property
    def core_offers_service(self):
        if self._core_offers_service is None:
            from bisq.core.api.core_offers_service import CoreOffersService

            self._core_offers_service = CoreOffersService(
                self._core_context,
                self.core_wallets_service,
            )
        return self._core_offers_service

    @property
    def core_payment_accounts_service(self):
        if self._core_payment_accounts_service is None:
            from bisq.core.api.core_payment_accounts_service import (
                CorePaymentAccountsService,
            )

            self._core_payment_accounts_service = CorePaymentAccountsService(
                self.core_wallets_service,
                self._config,
            )
        return self._core_payment_accounts_service

    @property
    def core_price_service(self):
        if self._core_price_service is None:
            from bisq.core.api.core_price_service import CorePriceService

            self._core_price_service = CorePriceService()
        return self._core_price_service

    @property
    def core_trades_service(self):
        if self._core_trades_service is None:
            from bisq.core.api.core_trades_service import CoreTradesService

            self._core_trades_service = CoreTradesService(
                self._core_context,
                self.core_wallets_service,
            )
        return self._core_trades_service

    @property
    def core_wallets_service(self):
        if self._core_wallets_service is None:
            from bisq.core.api.core_wallets_service import CoreWalletsService

            self._core_wallets_service = CoreWalletsService(
                self._core_context, self._user_manager
            )
        return self._core_wallets_service

    @property
    def grpc_server(self):
        if self._grpc_server is None:
            from bisq.daemon.grpc.grpc_server import GrpcServer

            self._grpc_server = GrpcServer(
                self._core_context,
                self._config,
                self.grpc_dispute_agents_service,
                self.grpc_help_service,
                self.grpc_offers_service,
                self.grpc_payment_accounts_service,
                self.grpc_price_service,
                self.grpc_shutdown_service,
                self.grpc_version_service,
                self.grpc_trades_service,
                self.grpc_wallets_service,
                self.grpc_dev_commands_service,
                self.grpc_user_manager_commands_service,
            )
        return self._grpc_server

    @property
    def grpc_exception_handler(self):
        if self._grpc_exception_handler is None:
            from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler

            self._grpc_exception_handler = GrpcExceptionHandler()
        return self._grpc_exception_handler

    @property
    def grpc_dispute_agents_service(self):
        if self._grpc_dispute_agents_service is None:
            from bisq.daemon.grpc.grpc_dispute_agent_service import (
                GrpcDisputeAgentsService,
            )

            self._grpc_dispute_agents_service = GrpcDisputeAgentsService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_dispute_agents_service

    @property
    def grpc_help_service(self):
        if self._grpc_help_service is None:
            from bisq.daemon.grpc.grpc_help_service import (
                GrpcHelpService,
            )

            self._grpc_help_service = GrpcHelpService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_help_service

    @property
    def grpc_offers_service(self):
        if self._grpc_offers_service is None:
            from bisq.daemon.grpc.grpc_offers_service import GrpcOffersService

            self._grpc_offers_service = GrpcOffersService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_offers_service

    @property
    def grpc_payment_accounts_service(self):
        if self._grpc_payment_accounts_service is None:
            from bisq.daemon.grpc.grpc_payment_accounts_service import (
                GrpcPaymentAccountsService,
            )

            self._grpc_payment_accounts_service = GrpcPaymentAccountsService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_payment_accounts_service

    @property
    def grpc_price_service(self):
        if self._grpc_price_service is None:
            from bisq.daemon.grpc.grpc_price_service import GrpcPriceService

            self._grpc_price_service = GrpcPriceService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_price_service

    @property
    def grpc_shutdown_service(self):
        if self._grpc_shutdown_service is None:
            from bisq.daemon.grpc.grpc_shutdown_service import GrpcShutdownService

            self._grpc_shutdown_service = GrpcShutdownService(
                self.grpc_exception_handler,
                self._graceful_shut_down_handler,
            )
        return self._grpc_shutdown_service

    @property
    def grpc_version_service(self):
        if self._grpc_version_service is None:
            from bisq.daemon.grpc.grpc_version_service import GrpcVersionService

            self._grpc_version_service = GrpcVersionService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_version_service

    @property
    def grpc_trades_service(self):
        if self._grpc_trades_service is None:
            from bisq.daemon.grpc.grpc_trades_service import GrpcTradesService

            self._grpc_trades_service = GrpcTradesService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_trades_service

    @property
    def grpc_wallets_service(self):
        if self._grpc_wallets_service is None:
            from bisq.daemon.grpc.grpc_wallets_service import GrpcWalletsService

            self._grpc_wallets_service = GrpcWalletsService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_wallets_service

    @property
    def grpc_dev_commands_service(self):
        if self._grpc_dev_commands_service is None:
            from bisq.daemon.grpc.grpc_dev_commands_service import (
                GrpcDevCommandsService,
            )

            self._grpc_dev_commands_service = GrpcDevCommandsService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_dev_commands_service

    @property
    def grpc_user_manager_commands_service(self):
        if self._grpc_user_manager_commands_service is None:
            from bisq.daemon.grpc.grpc_user_manager_commands_service import (
                GrpcUserManagerCommandsService,
            )

            self._grpc_user_manager_commands_service = GrpcUserManagerCommandsService(
                self.core_api,
                self.grpc_exception_handler,
                self._user_manager,
            )
        return self._grpc_user_manager_commands_service
