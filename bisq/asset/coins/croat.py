from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Croat(Coin):

    def __init__(self):
        super().__init__(
            name="Croat",
            ticker_symbol="CROAT",
            address_validator=RegexAddressValidator("^C[1-9A-HJ-NP-Za-km-z]{94}$"),
        )

