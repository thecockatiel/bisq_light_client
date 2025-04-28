from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import logger_context
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
    from bisq.core.user.user_manager import UserManager


class GrpcPaymentAccountsService(PaymentAccountsServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def CreatePaymentAccount(
        self, request: "CreatePaymentAccountRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                payment_account = self._core_api.create_payment_account(
                    user_context,
                    request.payment_account_form,
                )
                return CreatePaymentAccountReply(
                    payment_account=payment_account.to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetPaymentAccounts(
        self, request: "GetPaymentAccountsRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                payment_accounts = [
                    account.to_proto_message()
                    for account in self._core_api.get_payment_accounts(user_context)
                ]
                return GetPaymentAccountsReply(payment_accounts=payment_accounts)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetPaymentMethods(
        self, request: "GetPaymentMethodsRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                payment_methods = [
                    method.to_proto_message()
                    for method in self._core_api.get_fiat_payment_methods()
                ]
                return GetPaymentMethodsReply(payment_methods=payment_methods)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetPaymentAccountForm(
        self, request: "GetPaymentAccountFormRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                payment_account_form_json = self._core_api.get_payment_account_form(
                    request.payment_method_id
                )
                return GetPaymentAccountFormReply(
                    payment_account_form_json=payment_account_form_json
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def CreateCryptoCurrencyPaymentAccount(
        self,
        request: "CreateCryptoCurrencyPaymentAccountRequest",
        context: "ServicerContext",
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                payment_account = self._core_api.create_crypto_currency_payment_account(
                    user_context,
                    request.account_name,
                    request.currency_code,
                    request.address,
                    request.trade_instant,
                )
                return CreateCryptoCurrencyPaymentAccountReply(
                    payment_account=payment_account.to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetCryptoCurrencyPaymentMethods(
        self,
        request: "GetCryptoCurrencyPaymentMethodsRequest",
        context: "ServicerContext",
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                payment_methods = [
                    method.to_proto_message()
                    for method in self._core_api.get_crypto_currency_payment_methods()
                ]
                return GetCryptoCurrencyPaymentMethodsReply(payment_methods=payment_methods)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)
