from typing import TYPE_CHECKING
from bisq.core.locale.country_util import find_country_by_code
from bisq.core.locale.currency_util import get_currency_by_country_code
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.res import Res
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.mercado_pago_account_payload import (
    MercadoPagoAccountPayload,
)
from utils.python_helpers import classproperty

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class MercadoPagoAccount(CountryBasedPaymentAccount):
    SUPPORTED_COUNTRIES = [
        "AR",
        # other countries can be added later: "BR", "CL", "CO", "MX", "PE", "UY"
    ]

    MERCADO_PAGO_SITES = [
        "https://www.mercadopago.com.ar/"
        # shown when user is prompted to make payment.
        # other country specific sites can be added, see https://github.com/bisq-network/growth/issues/278
    ]

    @staticmethod
    def country_to_mercado_pago_site(country_code: str) -> str:
        try:
            index = MercadoPagoAccount.SUPPORTED_COUNTRIES.index(country_code)
            return MercadoPagoAccount.MERCADO_PAGO_SITES[index]
        except ValueError:
            return Res.get("payment.ask")

    @staticmethod
    def get_all_mercado_pago_countries():
        return [
            country
            for country_code in MercadoPagoAccount.SUPPORTED_COUNTRIES
            if (country := find_country_by_code(country_code)) is not None
        ]

    _SUPPORTED_CURRENCIES = []

    @classproperty
    def SUPPORTED_CURRENCIES() -> list["TradeCurrency"]:
        if not MercadoPagoAccount._SUPPORTED_CURRENCIES:
            MercadoPagoAccount._SUPPORTED_CURRENCIES = [
                get_currency_by_country_code(country_code)
                for country_code in MercadoPagoAccount.SUPPORTED_COUNTRIES
            ]
        return MercadoPagoAccount._SUPPORTED_CURRENCIES

    def __init__(self):
        super().__init__(PaymentMethod.MERCADO_PAGO)

    def create_payload(self) -> "PaymentAccountPayload":
        return MercadoPagoAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return MercadoPagoAccount.SUPPORTED_CURRENCIES

    @property
    def account_holder_id(self) -> str:
        return self._mercado_pago_account_payload.account_holder_id

    @account_holder_id.setter
    def account_holder_id(self, value: str) -> None:
        if value is None:
            value = ""
        self._mercado_pago_account_payload.account_holder_id = value

    @property
    def account_holder_name(self) -> str:
        return self._mercado_pago_account_payload.account_holder_name

    @account_holder_name.setter
    def account_holder_name(self, value: str) -> None:
        if value is None:
            value = ""
        self._mercado_pago_account_payload.account_holder_name = value

    def get_message_for_buyer(self) -> str:
        return "payment.generic.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.generic.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.mercadoPago.info.account"

    @property
    def _mercado_pago_account_payload(self):
        assert isinstance(self.payment_account_payload, MercadoPagoAccountPayload)
        return self.payment_account_payload
