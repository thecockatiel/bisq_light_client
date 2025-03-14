from typing import List, cast
from bisq.core.locale.currency_util import CurrencyUtil
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.crypto_currency_account_payload import (
    CryptoCurrencyAccountPayload,
)
from bisq.core.payment.payment_account import AssetAccount


class CryptoCurrencyAccount(AssetAccount):
    SUPPORTED_CURRENCIES: List[str] = CurrencyUtil.get_all_sorted_crypto_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.BLOCK_CHAINS)

    def create_payload(self):
        return CryptoCurrencyAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self):
        return CryptoCurrencyAccount.SUPPORTED_CURRENCIES

    @property
    def payment_account_payload(self):
        return cast(CryptoCurrencyAccountPayload, self.payment_account_payload)
