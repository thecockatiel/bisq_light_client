from bisq.core.locale.crypto_currency import CryptoCurrency
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.bsq_swap_account_payload import BsqSwapAccountPayload
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account import PaymentAccount 


# Placeholder account for Bsq swaps. We do not hold any data here, its just used to fit into the
# standard domain. We mimic the different trade protocol as a payment method with a dedicated account.
class BsqSwapAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = [CryptoCurrency("BSQ", "BSQ")]
    ID = "BsqSwapAccount"

    def __init__(self):
        super().__init__(PaymentMethod.BSQ_SWAP)

    def init(self):
        self.id = BsqSwapAccount.ID
        super().init()

    def create_payload(self) -> PaymentAccountPayload:
        return BsqSwapAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return BsqSwapAccount.SUPPORTED_CURRENCIES
