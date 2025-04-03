from typing import TYPE_CHECKING
from bisq.core.locale.currency_util import get_all_sorted_crypto_currencies
from bisq.core.payment.asset_account import AssetAccount
from bisq.core.payment.payload.instant_crypto_currency_account_payload import (
    InstantCryptoCurrencyPayload,
)
from bisq.core.payment.payload.payment_method import PaymentMethod


if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class InstantCryptoCurrencyAccount(AssetAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = list(
        get_all_sorted_crypto_currencies()
    )

    def __init__(self):
        super().__init__(PaymentMethod.BLOCK_CHAINS_INSTANT)

    def create_payload(self) -> "PaymentAccountPayload":
        return InstantCryptoCurrencyPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list["TradeCurrency"]:
        return InstantCryptoCurrencyAccount.SUPPORTED_CURRENCIES
