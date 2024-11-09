from bitcoinj.base.utils.fiat import Fiat
from bitcoinj.base.utils.monetary_format import (
    ALTCOIN_FRIENDLY_FORMAT,
    ALTCOIN_PLAIN_FORMAT,
)


class Altcoin(Fiat):
    SMALLEST_UNIT_EXPONENT = 8
    FRIENDLY_FORMAT = ALTCOIN_FRIENDLY_FORMAT
    PLAIN_FORMAT = ALTCOIN_PLAIN_FORMAT
