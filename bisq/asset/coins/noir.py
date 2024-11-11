from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Noir(Coin):

    def __init__(self):
        super().__init__(
            name="Noir",
            ticker_symbol="NOR",
            address_validator=RegexAddressValidator("^[Z][_A-z0-9]*([_A-z0-9])*$"),
        )

