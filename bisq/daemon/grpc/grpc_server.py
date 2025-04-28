from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING
from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.api.core_context import CoreContext
from bisq.daemon.grpc.grpc_dev_commands_service import GrpcDevCommandsService
from bisq.daemon.grpc.grpc_offers_service import GrpcOffersService
from bisq.daemon.grpc.grpc_payment_accounts_service import GrpcPaymentAccountsService
from bisq.daemon.grpc.grpc_price_service import GrpcPriceService
from bisq.daemon.grpc.grpc_shutdown_service import GrpcShutdownService
from bisq.daemon.grpc.grpc_trades_service import GrpcTradesService
from bisq.daemon.grpc.grpc_user_manager_commands_service import GrpcUserManagerCommandsService
from bisq.daemon.grpc.grpc_version_service import GrpcVersionService
from bisq.daemon.grpc.grpc_wallets_service import GrpcWalletsService
from bisq.daemon.grpc.interceptor.password_auth_interceptor import (
    PasswordAuthInterceptor,
)
import grpc
import grpc_pb2_grpc
import grpc_extra_pb2_grpc

if TYPE_CHECKING:
    from bisq.daemon.grpc.grpc_dispute_agent_service import GrpcDisputeAgentsService
    from bisq.daemon.grpc.grpc_help_service import GrpcHelpService


class GrpcServer:

    def __init__(
        self,
        core_context: "CoreContext",
        config: "Config",
        dispute_agents_service: "GrpcDisputeAgentsService",
        help_service: "GrpcHelpService",
        offers_service: "GrpcOffersService",
        payment_accounts_service: "GrpcPaymentAccountsService",
        price_service: "GrpcPriceService",
        shutdown_service: "GrpcShutdownService",
        version_service: "GrpcVersionService",
        trades_service: "GrpcTradesService",
        wallets_service: "GrpcWalletsService",
        dev_commands_service: "GrpcDevCommandsService",
        user_manager_commands_service: "GrpcUserManagerCommandsService",
    ):
        self.logger = get_ctx_logger(__name__)
        self.config = config
        self.server = grpc.server(
            ThreadPoolExecutor(max_workers=10, thread_name_prefix="grpc-server"),
            interceptors=(PasswordAuthInterceptor(self.config),),
        )
        grpc_pb2_grpc.add_DisputeAgentsServicer_to_server(
            dispute_agents_service, self.server
        )
        grpc_pb2_grpc.add_HelpServicer_to_server(help_service, self.server)
        grpc_pb2_grpc.add_OffersServicer_to_server(offers_service, self.server)
        grpc_pb2_grpc.add_PaymentAccountsServicer_to_server(
            payment_accounts_service, self.server
        )
        grpc_pb2_grpc.add_PriceServicer_to_server(price_service, self.server)
        grpc_pb2_grpc.add_ShutdownServerServicer_to_server(
            shutdown_service, self.server
        )
        grpc_pb2_grpc.add_GetVersionServicer_to_server(version_service, self.server)
        grpc_pb2_grpc.add_TradesServicer_to_server(trades_service, self.server)
        grpc_pb2_grpc.add_WalletsServicer_to_server(wallets_service, self.server)
        grpc_extra_pb2_grpc.add_DevCommandsServicer_to_server(dev_commands_service, self.server)
        grpc_extra_pb2_grpc.add_UserManagerCommandsServicer_to_server(user_manager_commands_service, self.server)
        # TODO: generate ssl certs and random password to file and use for cli to secure the connection
        self.server.add_insecure_port(f"127.0.0.1:{self.config.api_port}")
        core_context.is_api_user = True # TODO: set to false in GUI mode

    def start(self):
        self.server.start()
        self.logger.info(f"Grpc server started on port {self.config.api_port}")

    def shut_down(self):
        self.logger.info("Grpc server shutdown started")
        self.server.stop(0.5)
        self.server.wait_for_termination()
        self.logger.info("Grpc server shutdown complete")
