from typing import TYPE_CHECKING
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.imps_account_payload import ImpsAccountPayload

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class ImpsAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("INR")]

    def __init__(self):
        super().__init__(PaymentMethod.IMPS)

    def create_payload(self) -> "PaymentAccountPayload":
        return ImpsAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return ImpsAccount.SUPPORTED_CURRENCIES

    def get_message_for_buyer(self) -> str:
        return "payment.imps.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.imps.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.imps.info.account"
