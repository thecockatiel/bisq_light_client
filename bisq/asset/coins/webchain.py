from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Webchain(Coin):

    def __init__(self):
        super().__init__(
            name="Webchain",
            ticker_symbol="WEB",
            address_validator=RegexAddressValidator("^0x[0-9a-fA-F]{40}$"),
        )

