from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.revolute_account_payload import RevolutAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class RevolutAccount(PaymentAccount):

    # https://www.revolut.com/help/getting-started/exchanging-currencies/what-fiat-currencies-are-supported-for-holding-and-exchange
    SUPPORTED_CURRENCIES = [
        FiatCurrency("AED"),
        FiatCurrency("AUD"),
        FiatCurrency("BGN"),
        FiatCurrency("CAD"),
        FiatCurrency("CHF"),
        FiatCurrency("CZK"),
        FiatCurrency("DKK"),
        FiatCurrency("EUR"),
        FiatCurrency("GBP"),
        FiatCurrency("HKD"),
        FiatCurrency("HRK"),
        FiatCurrency("HUF"),
        FiatCurrency("ILS"),
        FiatCurrency("ISK"),
        FiatCurrency("JPY"),
        FiatCurrency("MAD"),
        FiatCurrency("MXN"),
        FiatCurrency("NOK"),
        FiatCurrency("NZD"),
        FiatCurrency("PLN"),
        FiatCurrency("QAR"),
        FiatCurrency("RON"),
        FiatCurrency("RSD"),
        FiatCurrency("RUB"),
        FiatCurrency("SAR"),
        FiatCurrency("SEK"),
        FiatCurrency("SGD"),
        FiatCurrency("THB"),
        FiatCurrency("TRY"),
        FiatCurrency("USD"),
        FiatCurrency("ZAR"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.REVOLUT)
        self.trade_currencies.extend(RevolutAccount.SUPPORTED_CURRENCIES)

    def create_payload(self):
        return RevolutAccountPayload(self.payment_method.id, self.id)

    @property
    def _revolute_account_payload(self):
        return cast(RevolutAccountPayload, self.payment_account_payload)

    @property
    def account_id(self):
        return self._revolute_account_payload.account_id

    @property
    def user_name(self):
        return self._revolute_account_payload.user_name

    @user_name.setter
    def user_name(self, value: str):
        self._revolute_account_payload.user_name = value

    @property
    def user_name_not_set(self):
        return self._revolute_account_payload.user_name_not_set

    @property
    def has_old_account_id(self):
        return self._revolute_account_payload.has_old_account_id

    def on_add_to_user(self):
        super().on_add_to_user()

        # At save we apply the userName to accountId in case it is empty for backward compatibility
        self._revolute_account_payload.maybe_apply_user_name_to_account_id()

    def get_supported_currencies(self):
        return RevolutAccount.SUPPORTED_CURRENCIES
