from typing import List
from bisq.core.locale.currency_util import CurrencyUtil
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.instant_crypto_currency_account_payload import (
    InstantCryptoCurrencyPayload,
)
from bisq.core.payment.payment_account import AssetAccount


class InstantCryptoCurrencyAccount(AssetAccount):
    SUPPORTED_CURRENCIES: List[str] = CurrencyUtil.get_all_sorted_crypto_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.BLOCK_CHAINS_INSTANT)

    def create_payload(self):
        return InstantCryptoCurrencyPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return InstantCryptoCurrencyAccount.SUPPORTED_CURRENCIES
