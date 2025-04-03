from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount


class IfscBasedAccount(CountryBasedPaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [FiatCurrency("INR")]

    def get_supported_currencies(self):
        return IfscBasedAccount.SUPPORTED_CURRENCIES
