from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.transferwise_usd_account_payload import (
    TransferwiseUsdAccountPayload,
)
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class TransferwiseUsdAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.TRANSFERWISE_USD)
        self.set_single_trade_currency(TransferwiseUsdAccount.SUPPORTED_CURRENCIES[0])

    def create_payload(self):
        return TransferwiseUsdAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return TransferwiseUsdAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(TransferwiseUsdAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(TransferwiseUsdAccountPayload, self.payment_account_payload).email = (
            value or ""
        )

    @property
    def holder_name(self):
        return cast(
            TransferwiseUsdAccountPayload, self.payment_account_payload
        ).holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        cast(
            TransferwiseUsdAccountPayload, self.payment_account_payload
        ).holder_name = (value or "")

    @property
    def beneficiary_address(self):
        return cast(
            TransferwiseUsdAccountPayload, self.payment_account_payload
        ).beneficiary_address

    @beneficiary_address.setter
    def beneficiary_address(self, value: str):
        cast(
            TransferwiseUsdAccountPayload, self.payment_account_payload
        ).beneficiary_address = (value or "")

    def get_message_for_buyer(self):
        return "payment.transferwiseUsd.info.buyer"

    def get_message_for_seller(self):
        return "payment.transferwiseUsd.info.seller"

    def get_message_for_account_creation(self):
        return "payment.transferwiseUsd.info.account"
