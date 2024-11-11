from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class SpaceCash(Coin):

    def __init__(self):
        super().__init__(
            name="SpaceCash",
            ticker_symbol="SPACE",
            address_validator=RegexAddressValidator("^([0-9a-z]{76})$"),
        )

