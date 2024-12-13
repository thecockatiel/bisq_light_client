from typing import TYPE_CHECKING, List, cast
from bisq.core.locale.currency_util import get_all_fiat_currencies
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payload.cash_by_mail_account_payload import CashByMailAccountPayload
from bisq.core.payment.payment_account import PaymentAccount

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.locale.trade_currency import TradeCurrency


class CashByMailAccount(PaymentAccount):
    SUPPORTED_CURRENCIES = get_all_fiat_currencies()

    def __init__(self):
        super().__init__(PaymentMethod.CASH_BY_MAIL)

    def create_payload(self) -> "PaymentAccountPayload":
        return CashByMailAccountPayload(self.payment_method.id, self.id)

    def get_supported_currencies(self) -> List['TradeCurrency']:
        return CashByMailAccount.SUPPORTED_CURRENCIES

    @property
    def postal_address(self) -> str:
        return cast(CashByMailAccountPayload, self.payment_account_payload).postal_address
    
    @postal_address.setter
    def postal_address(self, postal_address: str) -> None:
        cast(CashByMailAccountPayload, self.payment_account_payload).postal_address = postal_address
    
    @property
    def contact(self) -> str:
        return cast(CashByMailAccountPayload, self.payment_account_payload).contact
    
    @contact.setter
    def contact(self, contact: str) -> None:
        cast(CashByMailAccountPayload, self.payment_account_payload).contact = contact
        
    @property
    def extra_info(self) -> str:
        return cast(CashByMailAccountPayload, self.payment_account_payload).extra_info
    
    @extra_info.setter
    def extra_info(self, extra_info: str) -> None:
        cast(CashByMailAccountPayload, self.payment_account_payload).extra_info = extra_info
