from typing import cast, List
from bisq.core.locale.country import Country
from bisq.core.locale.country_util import CountryUtil
from bisq.core.locale.currency_util import CurrencyUtil
from bisq.core.locale.fiat_currency import FiatCurrency
from bisq.core.locale.res import Res
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.mercado_pago_account_payload import (
    MercadoPagoAccountPayload,
)
from bisq.core.payment.payment_account import CountryBasedPaymentAccount


class MercadoPagoAccount(CountryBasedPaymentAccount):
    SUPPORTED_COUNTRIES = ["AR"]
    MERCADO_PAGO_SITES = {"AR": "https://www.mercadopago.com.ar/"}

    @staticmethod
    def country_to_mercado_pago_site(country_code: str) -> str:
        return MercadoPagoAccount.MERCADO_PAGO_SITES.get(
            country_code, Res.get("payment.ask")
        )

    @staticmethod
    def get_all_mercado_pago_countries() -> List[Country]:
        return [
            CountryUtil.find_country_by_code(code)
            for code in MercadoPagoAccount.SUPPORTED_COUNTRIES
        ]

    @staticmethod
    def get_supported_currencies() -> List[FiatCurrency]:
        return [
            CurrencyUtil.get_currency_by_country_code(code)
            for code in MercadoPagoAccount.SUPPORTED_COUNTRIES
        ]

    def __init__(self):
        super().__init__(PaymentMethod.MERCADO_PAGO)

    def create_payload(self):
        return MercadoPagoAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return MercadoPagoAccount.get_supported_currencies()

    @property
    def account_holder_id(self):
        return cast(
            MercadoPagoAccountPayload, self.payment_account_payload
        ).account_holder_id

    @account_holder_id.setter
    def account_holder_id(self, value: str):
        cast(
            MercadoPagoAccountPayload, self.payment_account_payload
        ).account_holder_id = (value or "")

    @property
    def account_holder_name(self):
        return cast(
            MercadoPagoAccountPayload, self.payment_account_payload
        ).account_holder_name

    @account_holder_name.setter
    def account_holder_name(self, value: str):
        cast(
            MercadoPagoAccountPayload, self.payment_account_payload
        ).account_holder_name = (value or "")

    def get_message_for_buyer(self):
        return "payment.generic.info.buyer"

    def get_message_for_seller(self):
        return "payment.generic.info.seller"

    def get_message_for_account_creation(self):
        return "payment.mercadoPago.info.account"
