from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.imps_account_payload import ImpsAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class ImpsAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("INR")]

    def __init__(self):
        super().__init__(PaymentMethod.IMPS)

    def create_payload(self):
        return ImpsAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return ImpsAccount.SUPPORTED_CURRENCIES

    def get_message_for_buyer(self):
        return "payment.imps.info.buyer"

    def get_message_for_seller(self):
        return "payment.imps.info.seller"

    def get_message_for_account_creation(self):
        return "payment.imps.info.account"
