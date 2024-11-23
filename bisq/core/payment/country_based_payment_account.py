from abc import ABC
from typing import TYPE_CHECKING, Optional, cast

from bisq.core.locale.country_util import find_country_by_code
from bisq.core.payment.payload.country_based_payment_account_payload import CountryBasedPaymentAccountPayload
from bisq.core.payment.payment_account import PaymentAccount
from bisq.core.locale.country import Country 

if TYPE_CHECKING:
    from bisq.core.payment.payload.payment_method import PaymentMethod
    

class CountryBasedPaymentAccount(PaymentAccount, ABC):
    def __init__(self, payment_method: "PaymentMethod"):
        super().__init__(payment_method)
        self.country: Optional[Country] = None

    def get_country(self) -> Optional[Country]:
        if self.country is None:
            country_code = cast(CountryBasedPaymentAccountPayload, self.payment_account_payload).country_code
            country = find_country_by_code(country_code)
            if country:
                self.country = country
        return self.country

    def set_country(self, country: Country) -> None:
        self.country = country
        cast(CountryBasedPaymentAccountPayload, self.payment_account_payload).country_code = country.code

    def is_country_based_payment_account(self) -> bool:
        return True