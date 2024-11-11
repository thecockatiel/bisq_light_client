from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Askcoin(Coin):

    def __init__(self):
        super().__init__(
            name="Askcoin",
            ticker_symbol="ASK",
            address_validator=RegexAddressValidator("^[1-9][0-9]{0,11}$"),
        )

