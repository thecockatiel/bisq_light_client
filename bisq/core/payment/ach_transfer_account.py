from typing import cast
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.ach_transfer_account_payload import (
    AchTransferAccountPayload,
)
from bisq.core.payment.payload.bank_account_payload import BankAccountPayload
from bisq.core.payment.payment_account import CountryBasedPaymentAccount
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)


class AchTransferAccount(CountryBasedPaymentAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.ACH_TRANSFER)

    def create_payload(self):
        return AchTransferAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return AchTransferAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return cast(BankAccountPayload, self.payment_account_payload).bank_id

    @property
    def country_code(self):
        return self.country.code if self.country else ""

    @property
    def payload(self):
        return cast(AchTransferAccountPayload, self.payment_account_payload)

    def get_message_for_buyer(self):
        return "payment.achTransfer.info.buyer"

    def get_message_for_seller(self):
        return "payment.achTransfer.info.seller"

    def get_message_for_account_creation(self):
        return "payment.achTransfer.info.account"
