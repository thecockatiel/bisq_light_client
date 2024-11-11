from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Plenteum(Coin):

    def __init__(self):
        super().__init__(
            name="Plenteum",
            ticker_symbol="PLE",
            address_validator=RegexAddressValidator("^PLe[1-9A-Za-z^OIl]{95}$"),
        )

