from bisq.core.locale.currency_util import get_all_sorted_by_code_fiat_currencies
from bisq.core.locale.trade_currency import TradeCurrency
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.swift_account_payload import SwiftAccountPayload
from bisq.core.payment.payment_account import PaymentAccount


class SwiftAccount(PaymentAccount):
    SUPPORTED_CURRENCIES: list["TradeCurrency"] = (
        get_all_sorted_by_code_fiat_currencies()
    )

    def __init__(self):
        super().__init__(PaymentMethod.SWIFT)
        self.trade_currencies.extend(SwiftAccount.SUPPORTED_CURRENCIES)

    def create_payload(self) -> PaymentAccountPayload:
        return SwiftAccountPayload(self.payment_method.id, self.id)

    @property
    def payload(self):
        assert isinstance(self.payment_account_payload, SwiftAccountPayload)
        return self.payment_account_payload

    def get_message_for_buyer(self) -> str:
        return "payment.swift.info.buyer"

    def get_message_for_seller(self) -> str:
        return "payment.swift.info.seller"

    def get_message_for_account_creation(self) -> str:
        return "payment.swift.info.account"

    def get_supported_currencies(self) -> list[TradeCurrency]:
        return SwiftAccount.SUPPORTED_CURRENCIES
