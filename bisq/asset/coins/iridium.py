from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Iridium(Coin):

    def __init__(self):
        super().__init__(
            name="Iridium",
            ticker_symbol="IRD",
            address_validator=RegexAddressValidator("^ir[1-9A-Za-z^OIl]{95}$"),
        )
