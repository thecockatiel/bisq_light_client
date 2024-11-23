
from functools import total_ordering
from bisq.core.locale.currency_util import is_fiat_currency
from bisq.core.monetary.altcoin import Altcoin
from bisq.core.monetary.monetary_wrapper import MonetaryWrapper
from bisq.core.util.parsing_utils import ParsingUtils
from bitcoinj.base.monetary import Monetary
from bitcoinj.base.utils.fiat import Fiat


@total_ordering
class Volume(MonetaryWrapper):
    def __init__(self, monetary: Monetary) -> None:
        super().__init__(monetary)

    @staticmethod
    def parse(input_str: str, currency_code: str) -> 'Volume':
        cleaned = ParsingUtils.convert_chars_for_number(input_str)
        if is_fiat_currency(currency_code):
            return Volume(Fiat.parse_fiat(currency_code, cleaned))
        else:
            return Volume(Altcoin.parse_altcoin(currency_code, cleaned))

    def __lt__(self, other: 'Volume') -> bool:
        if self.currency_code != other.currency_code:
            return self.currency_code < other.currency_code
        return self.value < other.value

    def __eq__(self, other) -> bool:
        if not isinstance(other, Volume):
            return False
        if self.currency_code != other.currency_code:
            return False
        return self.value == other.value

    @property
    def currency_code(self) -> str:
        if isinstance(self.monetary, Altcoin):
            return self.monetary.currency_code
        if isinstance(self.monetary, Fiat):
            return self.monetary.currency_code
        raise ValueError("Unknown monetary type")

    def to_plain_string(self) -> str:
        if isinstance(self.monetary, Altcoin):
            return self.monetary.to_plain_string()
        if isinstance(self.monetary, Fiat):
            return self.monetary.to_plain_string()
        raise ValueError("Unknown monetary type")

    def __str__(self) -> str:
        return self.to_plain_string()

    def __repr__(self) -> str:
        return self.__str__()