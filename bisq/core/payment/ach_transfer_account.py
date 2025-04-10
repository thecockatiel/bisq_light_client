from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.ach_transfer_account_payload import (
    AchTransferAccountPayload,
)
from bisq.core.payment.same_country_restricted_bank_account import (
    SameCountryRestrictedBankAccount,
)

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class AchTransferAccount(CountryBasedPaymentAccount, SameCountryRestrictedBankAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("USD")]

    def __init__(self):
        super().__init__(PaymentMethod.ACH_TRANSFER)

    def create_payload(self) -> "PaymentAccountPayload":
        return AchTransferAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return AchTransferAccount.SUPPORTED_CURRENCIES

    @property
    def bank_id(self):
        return self.payload.bank_id

    @property
    def country_code(self):
        country = super().country
        return country.code if country else ""

    @property
    def payload(self):
        assert isinstance(self.payment_account_payload, AchTransferAccountPayload)
        return self.payment_account_payload

    def get_message_for_buyer(self) -> str:
        return "payment.achTransfer.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.achTransfer.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.achTransfer.info.account"
