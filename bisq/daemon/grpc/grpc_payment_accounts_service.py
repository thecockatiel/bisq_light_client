from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from grpc_pb2_grpc import PaymentAccountsServicer
from grpc_pb2 import (
    CreateCryptoCurrencyPaymentAccountReply,
    CreateCryptoCurrencyPaymentAccountRequest,
    CreatePaymentAccountRequest,
    CreatePaymentAccountReply,
    GetCryptoCurrencyPaymentMethodsReply,
    GetCryptoCurrencyPaymentMethodsRequest,
    GetPaymentAccountFormReply,
    GetPaymentAccountFormRequest,
    GetPaymentAccountsReply,
    GetPaymentAccountsRequest,
    GetPaymentMethodsReply,
    GetPaymentMethodsRequest,
)

if TYPE_CHECKING:
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcPaymentAccountsService(PaymentAccountsServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def CreatePaymentAccount(
        self, request: "CreatePaymentAccountRequest", context: "ServicerContext"
    ):
        try:
            payment_account = self.core_api.create_payment_account(
                request.payment_account_form
            )
            return CreatePaymentAccountReply(payment_account=payment_account)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetPaymentAccounts(
        self, request: "GetPaymentAccountsRequest", context: "ServicerContext"
    ):
        try:
            payment_accounts = [
                account.to_proto_message()
                for account in self.core_api.get_payment_accounts()
            ]
            return GetPaymentAccountsReply(payment_accounts=payment_accounts)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetPaymentMethods(
        self, request: "GetPaymentMethodsRequest", context: "ServicerContext"
    ):
        try:
            payment_methods = [
                method.to_proto_message()
                for method in self.core_api.get_fiat_payment_methods()
            ]
            return GetPaymentMethodsReply(payment_methods=payment_methods)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetPaymentAccountForm(
        self, request: "GetPaymentAccountFormRequest", context: "ServicerContext"
    ):
        try:
            payment_account_form_json = self.core_api.get_payment_account_form(
                request.payment_method_id
            )
            return GetPaymentAccountFormReply(
                payment_account_form_json=payment_account_form_json
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def CreateCryptoCurrencyPaymentAccount(
        self,
        request: "CreateCryptoCurrencyPaymentAccountRequest",
        context: "ServicerContext",
    ):
        try:
            payment_account = self.core_api.create_crypto_currency_payment_account(
                request.account_name,
                request.currency_code,
                request.address,
                request.trade_instant,
            )
            return CreateCryptoCurrencyPaymentAccountReply(
                payment_account=payment_account.to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetCryptoCurrencyPaymentMethods(
        self,
        request: "GetCryptoCurrencyPaymentMethodsRequest",
        context: "ServicerContext",
    ):
        try:
            payment_methods = [
                method.to_proto_message()
                for method in self.core_api.get_crypto_currency_payment_methods()
            ]
            return GetCryptoCurrencyPaymentMethodsReply(payment_methods=payment_methods)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    