from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class Remix(Coin):

    def __init__(self):
        super().__init__(
            name="Remix",
            ticker_symbol="RMX",
            address_validator=RegexAddressValidator("^((REMXi|SubRM)[1-9A-HJ-NP-Za-km-z]{94})$"),
        )

