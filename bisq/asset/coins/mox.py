from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class MoX(Coin):

    def __init__(self):
        super().__init__(
            name="MoX",
            ticker_symbol="MOX",
            address_validator=RegexAddressValidator("^X[1-9A-Za-z^OIl]{96}$"),
        )

