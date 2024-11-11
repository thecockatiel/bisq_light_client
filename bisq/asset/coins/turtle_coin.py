from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class TurtleCoin(Coin):

    def __init__(self):
        super().__init__(
            name="TurtleCoin",
            ticker_symbol="TRTL",
            address_validator=RegexAddressValidator("^TRTL[1-9A-Za-z^OIl]{95}$"),
        )

