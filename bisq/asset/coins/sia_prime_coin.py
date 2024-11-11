from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class SiaPrimeCoin(Coin):

    def __init__(self):
        super().__init__(
            name="SiaPrimeCoin",
            ticker_symbol="SCP",
            address_validator=RegexAddressValidator("^([0-9a-z]{76})$"),
        )

