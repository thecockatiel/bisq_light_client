import grpc
from bisq.cli import header_manipulator_client_interceptor
from grpc_pb2_grpc import (
    DisputeAgentsStub,
    HelpStub,
    OffersStub,
    PaymentAccountsStub,
    PriceStub,
    ShutdownServerStub,
    GetVersionStub,
    TradesStub,
    WalletsStub,
)
import atexit


class GrpcStubs:
    PASSWORD_KEY = "password"

    def __init__(self, api_host: str, api_port: int, password: str):

        header_adder_interceptor = (
            header_manipulator_client_interceptor.header_adder_interceptor(
                GrpcStubs.PASSWORD_KEY, password
            )
        )

        self.channel = grpc.insecure_channel(f"{api_host}:{api_port}")
        self.channel = grpc.intercept_channel(self.channel, header_adder_interceptor)
        atexit.register(self.close)

        self.dispute_agents_service = DisputeAgentsStub(self.channel)
        self.help_service = HelpStub(self.channel)
        self.version_service = GetVersionStub(self.channel)
        self.offers_service = OffersStub(self.channel)
        self.payment_accounts_service = PaymentAccountsStub(self.channel)
        self.price_service = PriceStub(self.channel)
        self.shutdown_service = ShutdownServerStub(self.channel)
        self.trades_service = TradesStub(self.channel)
        self.wallets_service = WalletsStub(self.channel)

    def close(self):
        if self.channel is not None:
            self.channel.close()
            self.channel = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
