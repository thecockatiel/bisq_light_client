from typing import cast
from bisq.core.locale.currency_util import CurrencyUtil
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.western_union_account_payload import (
    WesternUnionAccountPayload,
)
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class WesternUnionAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = CurrencyUtil.get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.WESTERN_UNION)

    def create_payload(self):
        return WesternUnionAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return WesternUnionAccount.SUPPORTED_CURRENCIES

    @property
    def email(self):
        return cast(WesternUnionAccountPayload, self.payment_account_payload).email

    @email.setter
    def email(self, value: str):
        cast(WesternUnionAccountPayload, self.payment_account_payload).email = (
            value or ""
        )

    @property
    def full_name(self):
        return cast(
            WesternUnionAccountPayload, self.payment_account_payload
        ).holder_name

    @full_name.setter
    def full_name(self, value: str):
        cast(WesternUnionAccountPayload, self.payment_account_payload).holder_name = (
            value or ""
        )

    @property
    def city(self):
        return cast(WesternUnionAccountPayload, self.payment_account_payload).city

    @city.setter
    def city(self, value: str):
        cast(WesternUnionAccountPayload, self.payment_account_payload).city = (
            value or ""
        )

    @property
    def state(self):
        return cast(WesternUnionAccountPayload, self.payment_account_payload).state

    @state.setter
    def state(self, value: str):
        cast(WesternUnionAccountPayload, self.payment_account_payload).state = (
            value or ""
        )
