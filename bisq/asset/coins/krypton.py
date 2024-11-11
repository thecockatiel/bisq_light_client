from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Krypton(Coin):

    def __init__(self):
        super().__init__(
            name="Krypton",
            ticker_symbol="ZOD",
            address_validator=RegexAddressValidator("^QQQ[1-9A-Za-z^OIl]{95}$"),
        )
