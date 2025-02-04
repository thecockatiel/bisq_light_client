from typing import TYPE_CHECKING
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2
import pb_pb2

if TYPE_CHECKING:
    from bisq.cli.grpc_stubs import GrpcStubs


class PaymentAccountsServiceRequest:

    def __init__(self, grpc_stubs: "GrpcStubs"):
        self.grpc_stubs = grpc_stubs

    def get_payment_methods(self) -> pb_pb2.PaymentMethod:
        request = grpc_pb2.GetPaymentMethodsRequest()
        response: grpc_pb2.GetPaymentMethodsReply = (
            self.grpc_stubs.payment_accounts_service.GetPaymentMethods(request)
        )
        return response.payment_methods

    # named getPaymentAcctFormAsJson in java
    def get_payment_account_form_as_json(self, payment_method_id: str) -> str:
        request = grpc_pb2.GetPaymentAccountFormRequest(
            payment_method_id=payment_method_id
        )
        response: grpc_pb2.GetPaymentAccountFormReply = (
            self.grpc_stubs.payment_accounts_service.GetPaymentAccountForm(request)
        )
        return response.payment_account_form_json

    def create_payment_account(self, json: str) -> pb_pb2.PaymentAccount:
        request = grpc_pb2.CreatePaymentAccountRequest(payment_account_form=json)
        response: grpc_pb2.CreatePaymentAccountReply = (
            self.grpc_stubs.payment_accounts_service.CreatePaymentAccount(request)
        )
        return response.payment_account

    def get_payment_accounts(self) -> list[pb_pb2.PaymentAccount]:
        request = grpc_pb2.GetPaymentAccountsRequest()
        response: grpc_pb2.GetPaymentAccountsReply = (
            self.grpc_stubs.payment_accounts_service.GetPaymentAccounts(request)
        )
        return response.payment_accounts

    def get_payment_account(self, account_name: str) -> pb_pb2.PaymentAccount:
        """
        Returns the first PaymentAccount found with the given name, or raises an
        IllegalArgumentException if not found. This method should be used with care;
        it will only return one PaymentAccount, and the account name must be an exact
        match on the name argument.
        Args:
            account_name (str): The name of the stored PaymentAccount to retrieve.
        Returns:
            pb_pb2.PaymentAccount: PaymentAccount with the given name.
        Raises:
            IllegalArgumentException: If no payment account with the given name is found.
        """

        payment_accounts = self.get_payment_accounts()
        for account in payment_accounts:
            if account.account_name == account_name:
                return account
        raise IllegalArgumentException(
            f"payment account with name '{account_name}' not found"
        )

    def create_crypto_currency_payment_account(
        self, account_name: str, currency_code: str, address: str, trade_instant: bool
    ) -> pb_pb2.PaymentAccount:
        request = grpc_pb2.CreateCryptoCurrencyPaymentAccountRequest(
            account_name=account_name,
            currency_code=currency_code,
            address=address,
            trade_instant=trade_instant,
        )
        response: grpc_pb2.CreateCryptoCurrencyPaymentAccountReply = (
            self.grpc_stubs.payment_accounts_service.CreateCryptoCurrencyPaymentAccount(
                request
            )
        )
        return response.payment_account

    def get_crypto_payment_methods(self) -> list[pb_pb2.PaymentMethod]:
        request = grpc_pb2.GetCryptoCurrencyPaymentMethodsRequest()
        response: grpc_pb2.GetCryptoCurrencyPaymentMethodsReply = (
            self.grpc_stubs.payment_accounts_service.GetCryptoCurrencyPaymentMethods(
                request
            )
        )
        return response.payment_methods
