from typing import TYPE_CHECKING, List, cast
from bisq.core.locale.currency_util import get_all_fiat_currencies
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.western_union_account_payload import (
    WesternUnionAccountPayload,
)

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class WesternUnionAccount(CountryBasedPaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.WESTERN_UNION)

    def create_payload(self) -> "PaymentAccountPayload":
        return WesternUnionAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> List["TradeCurrency"]:
        return WesternUnionAccount.SUPPORTED_CURRENCIES

    @property
    def email(self) -> str:
        return self._western_union_account_payload.email

    @email.setter
    def email(self, value: str) -> None:
        self._western_union_account_payload.email = value

    @property
    def full_name(self) -> str:
        return self._western_union_account_payload.holder_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        self._western_union_account_payload.holder_name = value

    @property
    def city(self) -> str:
        return self._western_union_account_payload.city

    @city.setter
    def city(self, value: str) -> None:
        self._western_union_account_payload.city = value

    @property
    def state(self) -> str:
        return self._western_union_account_payload.state

    @state.setter
    def state(self, value: str) -> None:
        self._western_union_account_payload.state = value

    @property
    def _western_union_account_payload(self):
        assert isinstance(self.payment_account_payload, WesternUnionAccountPayload)
        return self.payment_account_payload
