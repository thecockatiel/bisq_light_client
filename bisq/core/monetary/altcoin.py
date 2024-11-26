from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.base.utils.monetary_format import (
    ALTCOIN_FRIENDLY_FORMAT,
    ALTCOIN_PLAIN_FORMAT,
)


class Altcoin(Fiat):
    SMALLEST_UNIT_EXPONENT = 8
    FRIENDLY_FORMAT = ALTCOIN_FRIENDLY_FORMAT
    PLAIN_FORMAT = ALTCOIN_PLAIN_FORMAT

    @staticmethod
    def parse_altcoin(currency_code:str, input: str):
        from bisq.core.util.parsing_utils import ParsingUtils
        cleaned = ParsingUtils.convert_chars_for_number(input)
        return Altcoin.parse_fiat(currency_code, cleaned)
    
    def to_friendly_string(self) -> str:
        return Altcoin.FRIENDLY_FORMAT.code(0, self._currency_code).format(self)

    def to_plain_string(self) -> str:
        return Altcoin.PLAIN_FORMAT.format(self)
