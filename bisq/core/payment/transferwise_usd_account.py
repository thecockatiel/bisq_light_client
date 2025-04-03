from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.transferwise_usd_account_payload import (
    TransferwiseUsdAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod


class TransferwiseUsdAccount(CountryBasedPaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.TRANSFERWISE_USD)
        # this payment method is currently restricted to United States/USD
        self.set_single_trade_currency(TransferwiseUsdAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self) -> PaymentAccountPayload:
        return TransferwiseUsdAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return TransferwiseUsdAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return self._transferwise_usd_account_payload.email

    @email.setter
    def email(self, value: str):
        if value is None:
            value = ""
        self._transferwise_usd_account_payload.email = value

    @property
    def holder_name(self):
        return self._transferwise_usd_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        if value is None:
            value = ""
        self._transferwise_usd_account_payload.holder_name = value

    @property
    def beneficiary_address(self):
        return self._transferwise_usd_account_payload.beneficiary_address

    @beneficiary_address.setter
    def beneficiary_address(self, value: str):
        if value is None:
            value = ""
        self._transferwise_usd_account_payload.beneficiary_address = value

    def get_message_for_buyer(self) -> str:
        return "payment.transferwiseUsd.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.transferwiseUsd.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.transferwiseUsd.info.account"

    @property
    def _transferwise_usd_account_payload(self):
        assert isinstance(self.payment_account_payload, TransferwiseUsdAccountPayload)
        return self.payment_account_payload
