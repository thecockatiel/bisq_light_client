from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.us_postal_money_order_account_payload import (
    USPostalMoneyOrderAccountPayload,
)
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount


class USPostalMoneyOrderAccount(PaymentAccount):

    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [
        FiatCurrency("USD"),
    ]

    def __init__(self):
        super().__init__(PaymentMethod.US_POSTAL_MONEY_ORDER)
        self.set_single_trade_currency(
            USPostalMoneyOrderAccount.SUPPORTED_CURRENCIES[0]
        )

    def create_payload(self) -> PaymentAccountPayload:
        return USPostalMoneyOrderAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return USPostalMoneyOrderAccount.SUPPORTED_CURRENCIES

    @property
    def postal_address(self):
        return self._us_postal_money_order_account_payload.postal_address

    @postal_address.setter
    def postal_address(self, value: str):
        if value is None:
            value = ""
        self._us_postal_money_order_account_payload.postal_address = value

    @property
    def holder_name(self):
        return self._us_postal_money_order_account_payload.holder_name

    @holder_name.setter
    def holder_name(self, value: str):
        if value is None:
            value = ""
        self._us_postal_money_order_account_payload.holder_name = value

    @property
    def _us_postal_money_order_account_payload(self):
        assert isinstance(
            self.payment_account_payload, USPostalMoneyOrderAccountPayload
        )
        return self.payment_account_payload
