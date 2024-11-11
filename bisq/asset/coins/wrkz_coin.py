from bisq.asset.coin import Coin
from bisq.asset.regex_address_validator import RegexAddressValidator


class WrkzCoin(Coin):

    def __init__(self):
        super().__init__(
            name="WrkzCoin",
            ticker_symbol="WRKZ",
            address_validator=RegexAddressValidator("^Wrkz[1-9A-Za-z^OIl]{94}$"),
        )

